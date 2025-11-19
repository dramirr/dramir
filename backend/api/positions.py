"""
Positions API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from database.db import get_db_session
from database.models import Position, AuditLog

logger = logging.getLogger(__name__)
positions_bp = Blueprint('positions', __name__)


@positions_bp.route('', methods=['GET'])
@jwt_required()
def get_positions():
    """Get all positions"""
    try:
        with get_db_session() as db:
            positions = db.query(Position).all()
            return jsonify({
                'positions': [p.to_dict() for p in positions]
            })
    except Exception as e:
        logger.error(f"Get positions error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@positions_bp.route('/<int:position_id>', methods=['GET'])
@jwt_required()
def get_position(position_id):
    """Get position by ID"""
    try:
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            return jsonify(position.to_dict(include_criteria=True))
    except Exception as e:
        logger.error(f"Get position error: {str(e)}")
        return jsonify({'error': 'Failed to get position'}), 500


@positions_bp.route('', methods=['POST'])
@jwt_required()
def create_position():
    """Create new position"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.json
        
        title = data.get('title')
        description = data.get('description', '')
        threshold = data.get('threshold_percentage', 75)
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        with get_db_session() as db:
            position = Position(
                title=title,
                description=description,
                threshold_percentage=threshold,
                created_by=user_id,
                is_active=True
            )
            
            db.add(position)
            db.flush()
            
            audit_log = AuditLog(
                user_id=user_id,
                action='create_position',
                table_name='positions',
                record_id=position.id,
                changes_json={'title': title},
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Position created: {title} (ID: {position.id})")
            
            return jsonify({
                'message': 'Position created successfully',
                'position': position.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"Create position error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@positions_bp.route('/<int:position_id>', methods=['PUT'])
@jwt_required()
def update_position(position_id):
    """Update position"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.json
        
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            changes = {}
            
            if 'title' in data:
                changes['title'] = {'old': position.title, 'new': data['title']}
                position.title = data['title']
            
            if 'description' in data:
                position.description = data['description']
            
            if 'threshold_percentage' in data:
                changes['threshold'] = {'old': position.threshold_percentage, 'new': data['threshold_percentage']}
                position.threshold_percentage = data['threshold_percentage']
            
            if 'is_active' in data:
                changes['is_active'] = {'old': position.is_active, 'new': data['is_active']}
                position.is_active = data['is_active']
            
            position.updated_at = datetime.utcnow()
            
            audit_log = AuditLog(
                user_id=user_id,
                action='update_position',
                table_name='positions',
                record_id=position_id,
                changes_json=changes,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Position updated: {position.title} (ID: {position_id})")
            
            return jsonify({
                'message': 'Position updated successfully',
                'position': position.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Update position error: {str(e)}")
        return jsonify({'error': 'Failed to update position'}), 500


@positions_bp.route('/<int:position_id>', methods=['DELETE'])
@jwt_required()
def delete_position(position_id):
    """Delete position"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            title = position.title
            db.delete(position)
            
            audit_log = AuditLog(
                user_id=user_id,
                action='delete_position',
                table_name='positions',
                record_id=position_id,
                changes_json={'title': title},
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Position deleted: {title} (ID: {position_id})")
            
            return jsonify({'message': 'Position deleted successfully'})
            
    except Exception as e:
        logger.error(f"Delete position error: {str(e)}")
        return jsonify({'error': 'Failed to delete position'}), 500


@positions_bp.route('/<int:position_id>/stats', methods=['GET'])
@jwt_required()
def get_position_stats(position_id):
    """Get position statistics"""
    try:
        from database.models import Resume, ResumeScore
        
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            resumes = db.query(Resume).filter_by(position_id=position_id).all()
            
            total_resumes = len(resumes)
            qualified = 0
            rejected = 0
            pending = 0
            total_score = 0
            
            for resume in resumes:
                if resume.processing_status == 'completed' and resume.aggregate_score:
                    total_score += resume.aggregate_score.percentage
                    if resume.aggregate_score.status == 'Qualified':
                        qualified += 1
                    else:
                        rejected += 1
                else:
                    pending += 1
            
            avg_score = (total_score / (qualified + rejected)) if (qualified + rejected) > 0 else 0
            
            return jsonify({
                'position': position.to_dict(),
                'stats': {
                    'total_resumes': total_resumes,
                    'qualified': qualified,
                    'rejected': rejected,
                    'pending': pending,
                    'average_score': round(avg_score, 2)
                }
            })
            
    except Exception as e:
        logger.error(f"Get position stats error: {str(e)}")
        return jsonify({'error': 'Failed to get position stats'}), 500
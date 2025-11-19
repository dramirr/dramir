"""
Criteria API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from database.db import get_db_session
from database.models import Criterion, Position, AuditLog

logger = logging.getLogger(__name__)
criteria_bp = Blueprint('criteria', __name__)


@criteria_bp.route('/positions/<int:position_id>/criteria', methods=['GET'])
@jwt_required()
def get_criteria(position_id):
    """Get all criteria for a position"""
    try:
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            criteria = db.query(Criterion)\
                .filter_by(position_id=position_id)\
                .order_by(Criterion.display_order)\
                .all()
            
            return jsonify({
                'criteria': [c.to_dict() for c in criteria]
            })
            
    except Exception as e:
        logger.error(f"Get criteria error: {str(e)}")
        return jsonify({'error': 'Failed to get criteria'}), 500


@criteria_bp.route('/positions/<int:position_id>/criteria', methods=['POST'])
@jwt_required()
def create_criterion(position_id):
    """Create new criterion for a position"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        with get_db_session() as db:
            position = db.query(Position).filter_by(id=position_id).first()
            
            if not position:
                return jsonify({'error': 'Position not found'}), 404
            
            criterion = Criterion(
                position_id=position_id,
                criterion_key=data.get('criterion_key'),
                criterion_name=data.get('criterion_name'),
                category=data.get('category', 'core'),
                data_type=data.get('data_type'),
                weight=data.get('weight'),
                config_json=data.get('config_json', {}),
                is_required=data.get('is_required', False),
                display_order=data.get('display_order', 0)
            )
            
            db.add(criterion)
            db.flush()
            
            audit_log = AuditLog(
                user_id=user_id,
                action='create_criterion',
                table_name='criteria',
                record_id=criterion.id,
                changes_json={'criterion_name': criterion.criterion_name},
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Criterion created: {criterion.criterion_name} (ID: {criterion.id})")
            
            return jsonify({
                'message': 'Criterion created successfully',
                'criterion': criterion.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"Create criterion error: {str(e)}")
        return jsonify({'error': 'Failed to create criterion'}), 500


@criteria_bp.route('/criteria/<int:criterion_id>', methods=['GET'])
@jwt_required()
def get_criterion(criterion_id):
    """Get criterion by ID"""
    try:
        with get_db_session() as db:
            criterion = db.query(Criterion).filter_by(id=criterion_id).first()
            
            if not criterion:
                return jsonify({'error': 'Criterion not found'}), 404
            
            return jsonify(criterion.to_dict())
            
    except Exception as e:
        logger.error(f"Get criterion error: {str(e)}")
        return jsonify({'error': 'Failed to get criterion'}), 500


@criteria_bp.route('/criteria/<int:criterion_id>', methods=['PUT'])
@jwt_required()
def update_criterion(criterion_id):
    """Update criterion"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        with get_db_session() as db:
            criterion = db.query(Criterion).filter_by(id=criterion_id).first()
            
            if not criterion:
                return jsonify({'error': 'Criterion not found'}), 404
            
            changes = {}
            
            if 'criterion_name' in data:
                changes['criterion_name'] = {'old': criterion.criterion_name, 'new': data['criterion_name']}
                criterion.criterion_name = data['criterion_name']
            
            if 'criterion_key' in data:
                criterion.criterion_key = data['criterion_key']
            
            if 'category' in data:
                criterion.category = data['category']
            
            if 'data_type' in data:
                criterion.data_type = data['data_type']
            
            if 'weight' in data:
                changes['weight'] = {'old': criterion.weight, 'new': data['weight']}
                criterion.weight = data['weight']
            
            if 'config_json' in data:
                criterion.config_json = data['config_json']
            
            if 'is_required' in data:
                criterion.is_required = data['is_required']
            
            if 'display_order' in data:
                criterion.display_order = data['display_order']
            
            audit_log = AuditLog(
                user_id=user_id,
                action='update_criterion',
                table_name='criteria',
                record_id=criterion_id,
                changes_json=changes,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Criterion updated: {criterion.criterion_name} (ID: {criterion_id})")
            
            return jsonify({
                'message': 'Criterion updated successfully',
                'criterion': criterion.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Update criterion error: {str(e)}")
        return jsonify({'error': 'Failed to update criterion'}), 500


@criteria_bp.route('/criteria/<int:criterion_id>', methods=['DELETE'])
@jwt_required()
def delete_criterion(criterion_id):
    """Delete criterion"""
    try:
        user_id = get_jwt_identity()
        
        with get_db_session() as db:
            criterion = db.query(Criterion).filter_by(id=criterion_id).first()
            
            if not criterion:
                return jsonify({'error': 'Criterion not found'}), 404
            
            name = criterion.criterion_name
            db.delete(criterion)
            
            audit_log = AuditLog(
                user_id=user_id,
                action='delete_criterion',
                table_name='criteria',
                record_id=criterion_id,
                changes_json={'criterion_name': name},
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Criterion deleted: {name} (ID: {criterion_id})")
            
            return jsonify({'message': 'Criterion deleted successfully'})
            
    except Exception as e:
        logger.error(f"Delete criterion error: {str(e)}")
        return jsonify({'error': 'Failed to delete criterion'}), 500


@criteria_bp.route('/criteria/reorder', methods=['POST'])
@jwt_required()
def reorder_criteria():
    """Reorder criteria"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        criteria_order = data.get('criteria_order', [])
        
        with get_db_session() as db:
            for order_data in criteria_order:
                criterion_id = order_data.get('id')
                display_order = order_data.get('display_order')
                
                criterion = db.query(Criterion).filter_by(id=criterion_id).first()
                if criterion:
                    criterion.display_order = display_order
            
            audit_log = AuditLog(
                user_id=user_id,
                action='reorder_criteria',
                table_name='criteria',
                changes_json={'count': len(criteria_order)},
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Criteria reordered: {len(criteria_order)} items")
            
            return jsonify({'message': 'Criteria reordered successfully'})
            
    except Exception as e:
        logger.error(f"Reorder criteria error: {str(e)}")
        return jsonify({'error': 'Failed to reorder criteria'}), 500
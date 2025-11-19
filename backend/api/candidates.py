"""
Candidates API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from database.db import get_db_session
from database.models import Candidate, CandidateNote, AuditLog

logger = logging.getLogger(__name__)
candidates_bp = Blueprint('candidates', __name__)


@candidates_bp.route('', methods=['GET'])
@jwt_required()
def get_candidates():
    """Get all candidates"""
    try:
        with get_db_session() as db:
            candidates = db.query(Candidate)\
                .order_by(Candidate.last_updated.desc())\
                .all()
            
            return jsonify({
                'candidates': [c.to_dict() for c in candidates]
            })
            
    except Exception as e:
        logger.error(f"Get candidates error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>', methods=['GET'])
@jwt_required()
def get_candidate(candidate_id):
    """Get candidate profile"""
    try:
        with get_db_session() as db:
            candidate = db.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                return jsonify({'error': 'Candidate not found'}), 404
            
            result = candidate.to_dict(include_resumes=True)
            result['notes'] = [n.to_dict() for n in candidate.notes]
            
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Get candidate error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>/resumes', methods=['GET'])
@jwt_required()
def get_candidate_resumes(candidate_id):
    """Get all resumes for a candidate"""
    try:
        with get_db_session() as db:
            candidate = db.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                return jsonify({'error': 'Candidate not found'}), 404
            
            resumes = []
            for resume in candidate.resumes:
                resume_dict = resume.to_dict(include_details=True)
                if resume.aggregate_score:
                    resume_dict['score'] = resume.aggregate_score.to_dict()
                resumes.append(resume_dict)
            
            return jsonify({
                'candidate': candidate.to_dict(),
                'resumes': resumes
            })
            
    except Exception as e:
        logger.error(f"Get candidate resumes error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>/notes', methods=['GET'])
@jwt_required()
def get_candidate_notes(candidate_id):
    """Get all notes for a candidate"""
    try:
        with get_db_session() as db:
            candidate = db.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                return jsonify({'error': 'Candidate not found'}), 404
            
            notes = db.query(CandidateNote)\
                .filter_by(candidate_id=candidate_id)\
                .order_by(CandidateNote.created_at.desc())\
                .all()
            
            return jsonify({
                'notes': [n.to_dict() for n in notes]
            })
            
    except Exception as e:
        logger.error(f"Get candidate notes error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>/notes', methods=['POST'])
@jwt_required()
def add_candidate_note(candidate_id):
    """Add note to candidate"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        note_text = data.get('note_text')
        
        if not note_text:
            return jsonify({'error': 'Note text is required'}), 400
        
        with get_db_session() as db:
            candidate = db.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                return jsonify({'error': 'Candidate not found'}), 404
            
            note = CandidateNote(
                candidate_id=candidate_id,
                user_id=user_id,
                note_text=note_text
            )
            
            db.add(note)
            db.flush()
            
            audit_log = AuditLog(
                user_id=user_id,
                action='add_candidate_note',
                table_name='candidate_notes',
                record_id=note.id,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Note added to candidate {candidate_id} by user {user_id}")
            
            return jsonify({
                'message': 'Note added successfully',
                'note': note.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"Add candidate note error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_candidate_note(candidate_id, note_id):
    """Update candidate note"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        note_text = data.get('note_text')
        
        if not note_text:
            return jsonify({'error': 'Note text is required'}), 400
        
        with get_db_session() as db:
            note = db.query(CandidateNote).filter_by(
                id=note_id,
                candidate_id=candidate_id
            ).first()
            
            if not note:
                return jsonify({'error': 'Note not found'}), 404
            
            if note.user_id != user_id:
                return jsonify({'error': 'Not authorized to edit this note'}), 403
            
            note.note_text = note_text
            
            audit_log = AuditLog(
                user_id=user_id,
                action='update_candidate_note',
                table_name='candidate_notes',
                record_id=note_id,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Note {note_id} updated by user {user_id}")
            
            return jsonify({
                'message': 'Note updated successfully',
                'note': note.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Update candidate note error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/<int:candidate_id>/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_candidate_note(candidate_id, note_id):
    """Delete candidate note"""
    try:
        user_id = get_jwt_identity()
        
        with get_db_session() as db:
            note = db.query(CandidateNote).filter_by(
                id=note_id,
                candidate_id=candidate_id
            ).first()
            
            if not note:
                return jsonify({'error': 'Note not found'}), 404
            
            if note.user_id != user_id:
                return jsonify({'error': 'Not authorized to delete this note'}), 403
            
            db.delete(note)
            
            audit_log = AuditLog(
                user_id=user_id,
                action='delete_candidate_note',
                table_name='candidate_notes',
                record_id=note_id,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Note {note_id} deleted by user {user_id}")
            
            return jsonify({'message': 'Note deleted successfully'})
            
    except Exception as e:
        logger.error(f"Delete candidate note error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@candidates_bp.route('/search', methods=['GET'])
@jwt_required()
def search_candidates():
    """Search candidates by name or phone"""
    try:
        query = request.args.get('q', '')
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400
        
        with get_db_session() as db:
            candidates = db.query(Candidate).filter(
                (Candidate.full_name.ilike(f'%{query}%')) |
                (Candidate.phone.ilike(f'%{query}%')) |
                (Candidate.email.ilike(f'%{query}%'))
            ).all()
            
            return jsonify({
                'candidates': [c.to_dict() for c in candidates]
            })
            
    except Exception as e:
        logger.error(f"Search candidates error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
"""
Resumes API Endpoints - FULLY FIXED VERSION
Fixed issues:
- Session management in threads
- Lazy loading relationships
- Unicode encoding in logs
- Status endpoint implementation
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
import threading
import traceback
import json

logger = logging.getLogger(__name__)
resumes_bp = Blueprint('resumes', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def process_resume_async(resume_id, position_id):
    """
    Process resume in background thread with proper session management
    """
    try:
        # Import everything inside the thread
        from database.db import init_database, get_db_session
        from database.models import Resume, Candidate, ResumeData, Score, ResumeScore, Position, Criterion
        from services.extraction_service import ExtractionService
        from services.scoring_service import ScoringEngine
        from config import get_config
        
        # Initialize database for this thread if needed
        config = get_config()
        if not hasattr(threading.current_thread(), 'db_initialized'):
            init_database(config)
            threading.current_thread().db_initialized = True
        
        logger.info(f"[Thread-{threading.current_thread().name}] Starting AI processing for resume {resume_id}, position {position_id}")
        
        extraction_service = ExtractionService()
        scoring_service = ScoringEngine()
        
        # Use a new session for the entire processing
        with get_db_session() as db:
            # Fetch resume with all relationships eagerly loaded
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                logger.error(f"[Thread] Resume {resume_id} not found")
                return
            
            # Update status to processing
            resume.processing_status = 'processing'
            db.commit()
            db.refresh(resume)  # Refresh to ensure we have the latest state
            logger.info(f"[Thread] Resume {resume_id} status updated to: processing")
            
            # Get candidate within the same session
            candidate = db.query(Candidate).filter_by(id=resume.candidate_id).first()
            if not candidate:
                logger.error(f"[Thread] Candidate not found for resume {resume_id}")
                resume.processing_status = 'failed'
                db.commit()
                return
                
            try:
                # Extract data from resume
                logger.info(f"[Thread] Extracting data from file: {resume.file_path}")
                extracted_data = extraction_service.extract_from_file(
                    file_path=resume.file_path,
                    position_id=position_id
                )
                
                if not extracted_data:
                    logger.error(f"[Thread] No data extracted for resume {resume_id}")
                    resume.processing_status = 'failed'
                    db.commit()
                    return
                
                # Update candidate with extracted info
                if extracted_data.get('full_name'):
                    candidate.full_name = extracted_data['full_name']
                if extracted_data.get('email'):
                    candidate.email = extracted_data['email'] or ""
                if extracted_data.get('phone'):
                    candidate.phone = extracted_data['phone'] or candidate.phone
                
                candidate.last_updated = datetime.utcnow()
                db.commit()
                logger.info(f"[Thread] Candidate {candidate.id} updated: {candidate.full_name}")
                
                # Save or update ResumeData
                existing_data = db.query(ResumeData).filter_by(resume_id=resume_id).first()
                if existing_data:
                    existing_data.extracted_json = extracted_data
                else:
                    resume_data = ResumeData(
                        resume_id=resume_id,
                        extracted_json=extracted_data
                    )
                    db.add(resume_data)
                db.commit()
                logger.info(f"[Thread] Extracted data saved for resume {resume_id}")
                
                # Calculate scores
                logger.info(f"[Thread] Calculating scores for resume {resume_id}...")
                
                # Get position and criteria
                position = db.query(Position).filter_by(id=position_id).first()
                if not position:
                    logger.error(f"[Thread] Position {position_id} not found")
                    resume.processing_status = 'failed'
                    db.commit()
                    return
                
                criteria = db.query(Criterion).filter_by(position_id=position_id).all()
                if not criteria:
                    logger.warning(f"[Thread] No criteria found for position {position_id}")
                    resume.processing_status = 'completed'
                    resume.ai_analysis_json = {
                        'extracted_data': extracted_data,
                        'message': 'No criteria defined for scoring',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    db.commit()
                    return
                
                # Delete existing scores
                db.query(Score).filter_by(resume_id=resume_id).delete()
                db.query(ResumeScore).filter_by(resume_id=resume_id).delete()
                db.commit()
                
                # Calculate new scores
                individual_scores = []
                
                for criterion in criteria:
                    # Get value from extracted data
                    extracted_value = extracted_data.get(criterion.criterion_key)
                    
                    # Score the criterion
                    score_result = scoring_service.calculate_score(
                        criterion={
                            'data_type': criterion.data_type,
                            'weight': criterion.weight,
                            'config_json': criterion.config_json or {},
                            'criterion_key': criterion.criterion_key
                        },
                        extracted_value=extracted_value
                    )
                    
                    # Save individual score
                    score = Score(
                        resume_id=resume_id,
                        criterion_id=criterion.id,
                        awarded_points=score_result['awarded_points'],
                        max_points=score_result['max_points'],
                        score_multiplier=score_result.get('score_multiplier', 0),
                        extracted_value=str(extracted_value) if extracted_value is not None else None,
                        reasoning=score_result.get('reasoning', '')
                    )
                    db.add(score)
                    individual_scores.append(score_result)
                    
                    logger.info(f"[Thread] Scored {criterion.criterion_name}: {score_result['awarded_points']}/{score_result['max_points']}")
                
                # Calculate aggregate score
                aggregate_result = scoring_service.calculate_aggregate_score(
                    individual_scores,
                    threshold_percentage=position.threshold_percentage or 75
                )
                
                # Save aggregate score
                resume_score = ResumeScore(
                    resume_id=resume_id,
                    total_score=aggregate_result['total_score'],
                    max_possible_score=aggregate_result['max_possible_score'],
                    percentage=aggregate_result['percentage'],
                    status=aggregate_result['status'],
                    overall_assessment=aggregate_result.get('overall_assessment', '')
                )
                db.add(resume_score)
                
                # Save AI analysis to resume
                resume.ai_analysis_json = {
                    'extracted_data': extracted_data,
                    'aggregate_score': aggregate_result,
                    'individual_scores': individual_scores,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Update status to completed
                resume.processing_status = 'completed'
                db.commit()
                
                logger.info(f"[Thread] Processing completed successfully for resume {resume_id} - Score: {aggregate_result['percentage']}%")
                
            except Exception as process_error:
                logger.error(f"[Thread] Processing error for resume {resume_id}: {str(process_error)}")
                logger.error(traceback.format_exc())
                
                resume.processing_status = 'failed'
                resume.ai_analysis_json = {
                    'error': str(process_error),
                    'timestamp': datetime.utcnow().isoformat()
                }
                db.commit()
                
    except Exception as e:
        logger.error(f"[Thread] Fatal error processing resume {resume_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Try to mark as failed in a new session
        try:
            from database.db import get_db_session
            from database.models import Resume
            
            with get_db_session() as db:
                resume = db.query(Resume).filter_by(id=resume_id).first()
                if resume:
                    resume.processing_status = 'failed'
                    resume.ai_analysis_json = {
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    db.commit()
        except Exception as final_error:
            logger.error(f"[Thread] Could not update resume status: {str(final_error)}")


# Import main database components at module level
from database.db import get_db, get_db_session
from database.models import Resume, Position, Candidate, ResumeData, Score, ResumeScore, CandidateNote, AuditLog
from services.scoring_service import ScoringEngine
from services.question_generator import QuestionGenerator


@resumes_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload and process a resume"""
    try:
        # Validate file
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PDF, DOC, DOCX'}), 400
        
        # Get position ID
        position_id = request.form.get('position_id')
        if not position_id:
            return jsonify({'success': False, 'message': 'Position ID required'}), 400
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        logger.info(f"File saved: {filename} ({file_size} bytes)")
        
        with get_db_session() as db:
            # Verify position exists
            position = db.query(Position).filter_by(id=position_id).first()
            if not position:
                os.remove(filepath)  # Clean up file
                return jsonify({'success': False, 'message': 'Position not found'}), 404
            
            # Create or update candidate (temporary until AI extracts real info)
            temp_phone = f"temp_{os.urandom(5).hex()}"
            candidate = Candidate(
                phone=temp_phone,
                full_name="Processing...",
                email="",
                first_seen=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                total_submissions=1
            )
            db.add(candidate)
            db.flush()  # Get candidate ID
            
            # Create resume record
            resume = Resume(
                candidate_id=candidate.id,
                position_id=int(position_id),
                filename=filename,
                file_path=filepath,
                file_type=os.path.splitext(filename)[1],
                file_size=file_size,
                processing_status='pending',
                uploaded_by=get_jwt_identity(),
                uploaded_at=datetime.utcnow()
            )
            db.add(resume)
            db.flush()  # Get resume ID
            
            logger.info(f"Resume uploaded: ID {resume.id}, Candidate ID {candidate.id}")
            
            # Create audit log
            audit = AuditLog(
                user_id=get_jwt_identity(),
                action='upload_resume',
                table_name='resumes',
                record_id=resume.id,
                changes_json=json.dumps({
                    'filename': filename,
                    'position_id': position_id
                }),
                ip_address=request.remote_addr
            )
            db.add(audit)
            db.commit()
            
            # Refresh objects to get all data
            db.refresh(resume)
            db.refresh(candidate)
            
            # Start background processing
            thread = threading.Thread(
                target=process_resume_async,
                args=(resume.id, int(position_id)),
                name=f"resume-{resume.id}"
            )
            thread.start()
            logger.info(f"Background processing started for resume {resume.id}")
            
            # Return initial response
            return jsonify({
                'success': True,
                'message': 'Resume uploaded successfully',
                'resume': {
                    'id': resume.id,
                    'filename': resume.filename,
                    'processing_status': resume.processing_status,
                    'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None
                },
                'candidate': {
                    'id': candidate.id,
                    'full_name': candidate.full_name
                }
            }), 201
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>/status', methods=['GET'])
@jwt_required()
def get_resume_status(resume_id):
    """Get the current processing status of a resume"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
            # Check for scores if status is completed
            score_data = None
            if resume.processing_status == 'completed':
                resume_score = db.query(ResumeScore).filter_by(resume_id=resume_id).first()
                if resume_score:
                    score_data = {
                        'total_score': float(resume_score.total_score),
                        'max_possible_score': float(resume_score.max_possible_score),
                        'percentage': float(resume_score.percentage),
                        'status': resume_score.status,
                        'overall_assessment': resume_score.overall_assessment
                    }
            
            return jsonify({
                'success': True,
                'processing_status': resume.processing_status,
                'score': score_data,
                'ai_analysis': resume.ai_analysis_json if resume.processing_status == 'completed' else None
            })
            
    except Exception as e:
        logger.error(f"Error getting resume status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>', methods=['GET'])
@jwt_required()
def get_resume(resume_id):
    """Get full resume details"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
            # Get candidate
            candidate = db.query(Candidate).filter_by(id=resume.candidate_id).first()
            
            # Get position
            position = db.query(Position).filter_by(id=resume.position_id).first()
            
            # Get scores
            resume_score = db.query(ResumeScore).filter_by(resume_id=resume_id).first()
            individual_scores = db.query(Score).filter_by(resume_id=resume_id).all()
            
            # Get extracted data
            resume_data = db.query(ResumeData).filter_by(resume_id=resume_id).first()
            
            return jsonify({
                'success': True,
                'resume': {
                    'id': resume.id,
                    'filename': resume.filename,
                    'processing_status': resume.processing_status,
                    'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None
                },
                'candidate': candidate.to_dict() if candidate else None,
                'position': position.to_dict() if position else None,
                'score': {
                    'total_score': float(resume_score.total_score),
                    'max_possible_score': float(resume_score.max_possible_score),
                    'percentage': float(resume_score.percentage),
                    'status': resume_score.status,
                    'overall_assessment': resume_score.overall_assessment
                } if resume_score else None,
                'individual_scores': [
                    {
                        'criterion_id': score.criterion_id,
                        'awarded_points': float(score.awarded_points),
                        'max_points': float(score.max_points),
                        'extracted_value': score.extracted_value,
                        'reasoning': score.reasoning
                    } for score in individual_scores
                ],
                'extracted_data': resume_data.extracted_json if resume_data else None
            })
            
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('', methods=['GET'])
@jwt_required()
def list_resumes():
    """List all resumes with optional filters"""
    try:
        position_id = request.args.get('position_id', type=int)
        status = request.args.get('status')
        
        with get_db_session() as db:
            query = db.query(Resume).order_by(Resume.uploaded_at.desc())
            
            if position_id:
                query = query.filter_by(position_id=position_id)
            if status:
                query = query.filter_by(processing_status=status)
            
            resumes = query.all()
            
            result = []
            for resume in resumes:
                candidate = db.query(Candidate).filter_by(id=resume.candidate_id).first()
                position = db.query(Position).filter_by(id=resume.position_id).first()
                score = db.query(ResumeScore).filter_by(resume_id=resume.id).first()
                
                result.append({
                    'id': resume.id,
                    'filename': resume.filename,
                    'processing_status': resume.processing_status,
                    'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None,
                    'candidate': {
                        'id': candidate.id,
                        'full_name': candidate.full_name,
                        'email': candidate.email
                    } if candidate else None,
                    'position': {
                        'id': position.id,
                        'title': position.title
                    } if position else None,
                    'score': {
                        'percentage': float(score.percentage),
                        'status': score.status
                    } if score else None
                })
            
            return jsonify({
                'success': True,
                'resumes': result,
                'total': len(result)
            })
            
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_upload():
    """Upload multiple resumes at once"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        position_id = request.form.get('position_id')
        
        if not position_id:
            return jsonify({'success': False, 'message': 'Position ID required'}), 400
        
        if not files:
            return jsonify({'success': False, 'message': 'No files selected'}), 400
        
        results = []
        
        with get_db_session() as db:
            # Verify position exists
            position = db.query(Position).filter_by(id=position_id).first()
            if not position:
                return jsonify({'success': False, 'message': 'Position not found'}), 404
            
            for file in files:
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename):
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': 'Invalid file type'
                    })
                    continue
                
                try:
                    # Save file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(file.filename)
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    file_size = os.path.getsize(filepath)
                    
                    # Create candidate
                    temp_phone = f"temp_{os.urandom(5).hex()}"
                    candidate = Candidate(
                        phone=temp_phone,
                        full_name="Processing...",
                        email="",
                        first_seen=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        total_submissions=1
                    )
                    db.add(candidate)
                    db.flush()
                    
                    # Create resume
                    resume = Resume(
                        candidate_id=candidate.id,
                        position_id=int(position_id),
                        filename=filename,
                        file_path=filepath,
                        file_type=os.path.splitext(filename)[1],
                        file_size=file_size,
                        processing_status='pending',
                        uploaded_by=get_jwt_identity(),
                        uploaded_at=datetime.utcnow()
                    )
                    db.add(resume)
                    db.flush()
                    
                    # Start processing
                    thread = threading.Thread(
                        target=process_resume_async,
                        args=(resume.id, int(position_id)),
                        name=f"resume-{resume.id}"
                    )
                    thread.start()
                    
                    results.append({
                        'filename': file.filename,
                        'success': True,
                        'resume_id': resume.id
                    })
                    
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': str(e)
                    })
            
            db.commit()
        
        return jsonify({
            'success': True,
            'results': results,
            'total_uploaded': sum(1 for r in results if r['success'])
        }), 201
        
    except Exception as e:
        logger.error(f"Bulk upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>/questions', methods=['GET'])
@jwt_required()
def get_interview_questions(resume_id):
    """Generate interview questions for a resume"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
            if resume.processing_status != 'completed':
                return jsonify({'success': False, 'message': 'Resume processing not completed'}), 400
            
            # Get extracted data
            resume_data = db.query(ResumeData).filter_by(resume_id=resume_id).first()
            if not resume_data:
                return jsonify({'success': False, 'message': 'No extracted data found'}), 404
            
            # Get position
            position = db.query(Position).filter_by(id=resume.position_id).first()
            
            # Generate questions
            question_gen = QuestionGenerator()
            questions = question_gen.generate_questions(
                resume_data=resume_data.extracted_json,
                position_title=position.title if position else "General"
            )
            
            return jsonify({
                'success': True,
                'questions': questions
            })
            
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>', methods=['DELETE'])
@jwt_required()
def delete_resume(resume_id):
    """Delete a resume and its associated data"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
            # Delete file if exists
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
            
            # Delete database records (cascading will handle related tables)
            db.delete(resume)
            
            # Create audit log
            audit = AuditLog(
                user_id=get_jwt_identity(),
                action='delete_resume',
                table_name='resumes',
                record_id=resume_id,
                changes_json=json.dumps({'filename': resume.filename}),
                ip_address=request.remote_addr
            )
            db.add(audit)
            db.commit()
            
            return jsonify({'success': True, 'message': 'Resume deleted successfully'})
            
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
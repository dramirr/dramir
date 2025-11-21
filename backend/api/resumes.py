"""
Resumes API Endpoints - FULLY FIXED VERSION
✅ Fixed: Duplicate candidate handling (UNIQUE constraint error)
✅ Fixed: Proper status updates
✅ Fixed: Better error handling
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
import hashlib

logger = logging.getLogger(__name__)
resumes_bp = Blueprint('resumes', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def process_resume_async(resume_id, position_id):
    """
    ✅ FIXED: Process resume in background thread
    """
    from database.db import get_db_session
    from database.models import Resume, Candidate, ResumeData, Score, ResumeScore, Position, Criterion
    from services.extraction_service import ExtractionService
    from services.scoring_service import ScoringEngine
    from config import get_config
    
    config = get_config()
    thread_name = threading.current_thread().name
    
    logger.info(f"[{thread_name}] 🚀 Starting AI processing for resume {resume_id}, position {position_id}")
    
    try:
        # Initialize services
        extraction_service = ExtractionService()
        scoring_service = ScoringEngine()
        
        # ✅ Use fresh session for entire processing
        with get_db_session() as db:
            # Load resume
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                logger.error(f"[{thread_name}] Resume {resume_id} not found")
                return
            
            # Update status to processing
            resume.processing_status = 'processing'
            db.commit()
            logger.info(f"[{thread_name}] ✅ Resume {resume_id} status: processing")
            
            # ✅ Get candidate_id and file_path BEFORE extraction
            candidate_id = resume.candidate_id
            file_path = resume.file_path
            
            try:
                # ✅ Extract data from resume
                logger.info(f"[{thread_name}] 📄 Extracting data from: {file_path}")
                
                extracted_data = extraction_service.extract_from_file(
                    file_path=file_path,
                    position_id=position_id
                )
                
                if not extracted_data:
                    raise ValueError("No data extracted from resume")
                
                logger.info(f"[{thread_name}] ✅ Data extracted successfully")
                logger.info(f"[{thread_name}] 👤 Candidate: {extracted_data.get('full_name', 'Unknown')}")
                
                # ✅ Update candidate with extracted phone
                candidate = db.query(Candidate).filter_by(id=candidate_id).first()
                if not candidate:
                    raise ValueError(f"Candidate {candidate_id} not found")
                
                # Update candidate info
                if extracted_data.get('full_name'):
                    candidate.full_name = extracted_data['full_name']
                if extracted_data.get('email'):
                    candidate.email = extracted_data['email'] or ""
                
                # ✅ CRITICAL: Handle phone update carefully
                extracted_phone = extracted_data.get('phone')
                if extracted_phone and extracted_phone != candidate.phone:
                    # Check if new phone already exists
                    existing = db.query(Candidate).filter_by(phone=extracted_phone).first()
                    if existing and existing.id != candidate_id:
                        logger.warning(f"[{thread_name}] Phone {extracted_phone} already exists for candidate {existing.id}")
                        # Keep temporary phone, don't update
                    else:
                        candidate.phone = extracted_phone
                
                candidate.last_updated = datetime.utcnow()
                db.commit()
                
                logger.info(f"[{thread_name}] ✅ Candidate updated: {candidate.full_name}")
                
                # ✅ Save extracted data
                existing_data = db.query(ResumeData).filter_by(resume_id=resume_id).first()
                if existing_data:
                    existing_data.extracted_json = extracted_data
                    existing_data.extracted_at = datetime.utcnow()
                else:
                    resume_data = ResumeData(
                        resume_id=resume_id,
                        extracted_json=extracted_data
                    )
                    db.add(resume_data)
                db.commit()
                
                logger.info(f"[{thread_name}] ✅ Extracted data saved to database")
                
                # ✅ Get position and criteria
                position = db.query(Position).filter_by(id=position_id).first()
                if not position:
                    raise ValueError(f"Position {position_id} not found")
                
                criteria = db.query(Criterion).filter_by(position_id=position_id).order_by(Criterion.display_order).all()
                if not criteria:
                    logger.warning(f"[{thread_name}] No criteria found for position {position_id}")
                    resume.processing_status = 'completed'
                    resume.ai_analysis_json = {
                        'extracted_data': extracted_data,
                        'message': 'No criteria defined for scoring',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    db.commit()
                    logger.info(f"[{thread_name}] ✅ Completed (no scoring - no criteria)")
                    return
                
                # ✅ Delete existing scores
                db.query(Score).filter_by(resume_id=resume_id).delete()
                db.query(ResumeScore).filter_by(resume_id=resume_id).delete()
                db.commit()
                
                logger.info(f"[{thread_name}] 🧮 Calculating scores for {len(criteria)} criteria...")
                
                # ✅ Calculate scores
                individual_scores = []
                for idx, criterion in enumerate(criteria, 1):
                    extracted_value = extracted_data.get(criterion.criterion_key)
                    
                    score_result = scoring_service.calculate_score(
                        criterion={
                            'data_type': criterion.data_type,
                            'weight': criterion.weight,
                            'config_json': criterion.config_json or {},
                            'criterion_key': criterion.criterion_key
                        },
                        extracted_value=extracted_value
                    )
                    
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
                    
                    logger.info(f"[{thread_name}] [{idx}/{len(criteria)}] {criterion.criterion_name}: {score_result['awarded_points']:.1f}/{score_result['max_points']}")
                
                # ✅ Calculate aggregate score
                aggregate_result = scoring_service.calculate_aggregate_score(
                    individual_scores,
                    threshold_percentage=position.threshold_percentage or 75
                )
                
                logger.info(f"[{thread_name}] 📊 Aggregate Score: {aggregate_result['percentage']:.2f}% - Status: {aggregate_result['status']}")
                
                # ✅ Save aggregate score
                resume_score = ResumeScore(
                    resume_id=resume_id,
                    total_score=aggregate_result['total_score'],
                    max_possible_score=aggregate_result['max_possible_score'],
                    percentage=aggregate_result['percentage'],
                    status=aggregate_result['status'],
                    overall_assessment=aggregate_result.get('overall_assessment', '')
                )
                db.add(resume_score)
                
                # ✅ Save AI analysis
                resume.ai_analysis_json = {
                    'extracted_data': extracted_data,
                    'aggregate_score': aggregate_result,
                    'individual_scores': individual_scores,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # ✅ Mark as completed
                resume.processing_status = 'completed'
                db.commit()
                
                logger.info(f"[{thread_name}] ✅✅✅ Resume {resume_id} processing COMPLETED - Score: {aggregate_result['percentage']:.2f}%")
                
            except Exception as process_error:
                logger.error(f"[{thread_name}] ❌ Processing error: {str(process_error)}")
                logger.error(traceback.format_exc())
                
                # Mark as failed
                resume.processing_status = 'failed'
                resume.ai_analysis_json = {
                    'error': str(process_error),
                    'error_type': type(process_error).__name__,
                    'timestamp': datetime.utcnow().isoformat()
                }
                db.commit()
                
    except Exception as fatal_error:
        logger.error(f"[{thread_name}] ❌❌❌ FATAL ERROR: {str(fatal_error)}")
        logger.error(traceback.format_exc())
        
        # Try to mark as failed in new session
        try:
            from database.db import get_db_session
            from database.models import Resume
            
            with get_db_session() as db:
                resume = db.query(Resume).filter_by(id=resume_id).first()
                if resume:
                    resume.processing_status = 'failed'
                    resume.ai_analysis_json = {
                        'error': str(fatal_error),
                        'error_type': type(fatal_error).__name__,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    db.commit()
        except Exception as final_error:
            logger.error(f"[{thread_name}] Could not update resume status: {str(final_error)}")

            
# Import at module level
from database.db import get_db_session
from database.models import Resume, Position, Candidate, ResumeData, Score, ResumeScore, AuditLog


@resumes_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """✅ FIXED: Upload and process a resume with proper duplicate handling"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        position_id = request.form.get('position_id')
        if not position_id:
            return jsonify({'success': False, 'message': 'Position ID required'}), 400
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        logger.info(f"📁 File saved: {filename} ({file_size} bytes)")
        
        with get_db_session() as db:
            # Verify position
            position = db.query(Position).filter_by(id=position_id).first()
            if not position:
                os.remove(filepath)
                return jsonify({'success': False, 'message': 'Position not found'}), 404
            
            # ✅ CRITICAL FIX: Create temporary phone that's guaranteed unique
            temp_phone = f"temp_{hashlib.md5(f"{filename}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:15]}"
            
            # ✅ Double-check uniqueness
            while db.query(Candidate).filter_by(phone=temp_phone).first():
                temp_phone = f"temp_{hashlib.md5(f"{filename}{datetime.utcnow().isoformat()}{os.urandom(8)}".encode()).hexdigest()[:15]}"
            
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
            
            resume_id = resume.id
            candidate_id = candidate.id
            
            logger.info(f"✅ Resume uploaded: ID {resume_id}, Candidate ID {candidate_id}")
            
            # Audit log
            audit = AuditLog(
                user_id=get_jwt_identity(),
                action='upload_resume',
                table_name='resumes',
                record_id=resume_id,
                changes_json=json.dumps({'filename': filename, 'position_id': position_id}),
                ip_address=request.remote_addr
            )
            db.add(audit)
            db.commit()
            
            # Start background processing
            thread = threading.Thread(
                target=process_resume_async,
                args=(resume_id, int(position_id)),
                name=f"resume-{resume_id}",
                daemon=True
            )
            thread.start()
            logger.info(f"🚀 Background thread started for resume {resume_id}")
            
            return jsonify({
                'success': True,
                'message': 'Resume uploaded successfully',
                'resume': {
                    'id': resume_id,
                    'filename': filename,
                    'processing_status': 'pending',
                    'uploaded_at': datetime.utcnow().isoformat()
                },
                'candidate': {
                    'id': candidate_id,
                    'full_name': 'Processing...'
                }
            }), 201
            
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>/status', methods=['GET'])
@jwt_required()
def get_resume_status(resume_id):
    """✅ Get resume processing status"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
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
        logger.error(f"❌ Error getting status: {str(e)}")
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
            
            candidate = db.query(Candidate).filter_by(id=resume.candidate_id).first()
            position = db.query(Position).filter_by(id=resume.position_id).first()
            resume_score = db.query(ResumeScore).filter_by(resume_id=resume_id).first()
            individual_scores = db.query(Score).filter_by(resume_id=resume_id).all()
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
                'score': resume_score.to_dict() if resume_score else None,
                'individual_scores': [s.to_dict() for s in individual_scores],
                'extracted_data': resume_data.extracted_json if resume_data else None
            })
            
    except Exception as e:
        logger.error(f"❌ Error getting resume: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('', methods=['GET'])
@jwt_required()
def list_resumes():
    """List all resumes"""
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
                    'candidate': candidate.to_dict() if candidate else None,
                    'position': position.to_dict() if position else None,
                    'score': score.to_dict() if score else None
                })
            
            return jsonify({
                'success': True,
                'resumes': result,
                'total': len(result)
            })
            
    except Exception as e:
        logger.error(f"❌ Error listing resumes: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@resumes_bp.route('/<int:resume_id>', methods=['DELETE'])
@jwt_required()
def delete_resume(resume_id):
    """Delete resume"""
    try:
        with get_db_session() as db:
            resume = db.query(Resume).filter_by(id=resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': 'Resume not found'}), 404
            
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
            
            db.delete(resume)
            
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
            
            return jsonify({'success': True, 'message': 'Resume deleted'})
            
    except Exception as e:
        logger.error(f"❌ Error deleting resume: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
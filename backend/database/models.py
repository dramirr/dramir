"""
Database Models for TalentRadar v2 - FIXED VERSION
Fixed: ResumeData to handle JSON properly
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, DECIMAL, JSON, UniqueConstraint, Index, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='viewer')  # admin, recruiter, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    positions = relationship('Position', back_populates='creator')
    resumes_uploaded = relationship('Resume', back_populates='uploader')
    notes = relationship('CandidateNote', back_populates='author')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Position(Base):
    """Job position model"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    threshold_percentage = Column(Integer, default=75)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship('User', back_populates='positions')
    criteria = relationship('Criterion', back_populates='position', cascade='all, delete-orphan')
    resumes = relationship('Resume', back_populates='position')
    
    def to_dict(self, include_criteria=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'threshold_percentage': self.threshold_percentage,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_criteria:
            data['criteria'] = [c.to_dict() for c in self.criteria]
        
        return data


class Criterion(Base):
    """Evaluation criteria model with flexible configuration"""
    __tablename__ = 'criteria'
    __table_args__ = (
        UniqueConstraint('position_id', 'criterion_key', name='uq_position_criterion'),
    )
    
    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id', ondelete='CASCADE'), nullable=False)
    criterion_key = Column(String(100), nullable=False)
    criterion_name = Column(String(200), nullable=False)
    category = Column(String(50))  # technical, experience, education, etc.
    data_type = Column(String(20), nullable=False)  # keywords, years, percentage, boolean
    weight = Column(Integer, default=1)
    config_json = Column(JSON)  # Flexible configuration for scoring
    is_required = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    position = relationship('Position', back_populates='criteria')
    scores = relationship('Score', back_populates='criterion')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'position_id': self.position_id,
            'criterion_key': self.criterion_key,
            'criterion_name': self.criterion_name,
            'category': self.category,
            'data_type': self.data_type,
            'weight': self.weight,
            'config_json': self.config_json,
            'is_required': self.is_required,
            'display_order': self.display_order
        }


class Candidate(Base):
    """Candidate model with de-duplication"""
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, index=True)  # Primary unique identifier
    full_name = Column(String(200), nullable=False)
    email = Column(String(100))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    total_submissions = Column(Integer, default=0)
    notes_summary = Column(Text)
    
    # Relationships
    resumes = relationship('Resume', back_populates='candidate')
    notes = relationship('CandidateNote', back_populates='candidate', cascade='all, delete-orphan')
    
    def to_dict(self, include_resumes=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'phone': self.phone,
            'full_name': self.full_name,
            'email': self.email,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'total_submissions': self.total_submissions,
            'notes_summary': self.notes_summary
        }
        
        if include_resumes:
            data['resumes'] = [r.to_dict() for r in self.resumes]
        
        return data


class Resume(Base):
    """Resume submission model"""
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False)
    position_id = Column(Integer, ForeignKey('positions.id'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20))
    file_size = Column(Integer)
    processing_status = Column(String(50), default='pending', index=True)  # pending, processing, completed, failed
    ai_analysis_json = Column(JSON)  # Full AI response
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship('Candidate', back_populates='resumes')
    position = relationship('Position', back_populates='resumes')
    uploader = relationship('User', back_populates='resumes_uploaded')
    extracted_data = relationship('ResumeData', back_populates='resume', cascade='all, delete-orphan', uselist=False)
    scores = relationship('Score', back_populates='resume', cascade='all, delete-orphan')
    aggregate_score = relationship('ResumeScore', back_populates='resume', uselist=False, cascade='all, delete-orphan')
    interview_questions = relationship('InterviewQuestion', back_populates='resume', cascade='all, delete-orphan')
    
    def to_dict(self, include_details=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'position_id': self.position_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'processing_status': self.processing_status,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
        
        if include_details:
            data['candidate'] = self.candidate.to_dict() if self.candidate else None
            data['position'] = self.position.to_dict() if self.position else None
            data['aggregate_score'] = self.aggregate_score.to_dict() if self.aggregate_score else None
        
        return data


class ResumeData(Base):
    """Extracted data from resumes - FIXED to store as JSON"""
    __tablename__ = 'resume_data'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, unique=True)
    extracted_json = Column(JSON, nullable=False)  # Store all extracted data as JSON
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship('Resume', back_populates='extracted_data', uselist=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'resume_id': self.resume_id,
            'extracted_data': self.extracted_json,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None
        }


class Score(Base):
    """Individual criterion score"""
    __tablename__ = 'scores'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    criterion_id = Column(Integer, ForeignKey('criteria.id'))
    extracted_value = Column(Text)
    awarded_points = Column(Float)
    max_points = Column(Float)
    score_multiplier = Column(Float, default=0)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship('Resume', back_populates='scores')
    criterion = relationship('Criterion', back_populates='scores')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'criterion_id': self.criterion_id,
            'extracted_value': self.extracted_value,
            'awarded_points': float(self.awarded_points) if self.awarded_points else 0,
            'max_points': float(self.max_points) if self.max_points else 0,
            'score_multiplier': float(self.score_multiplier) if self.score_multiplier else 0,
            'reasoning': self.reasoning
        }


class ResumeScore(Base):
    """Aggregate score for a resume"""
    __tablename__ = 'resume_scores'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, unique=True)
    total_score = Column(Float, nullable=False)
    max_possible_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    status = Column(String(20))  # passed, failed, review_needed
    overall_assessment = Column(Text)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship('Resume', back_populates='aggregate_score', uselist=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'resume_id': self.resume_id,
            'total_score': float(self.total_score),
            'max_possible_score': float(self.max_possible_score),
            'percentage': float(self.percentage),
            'status': self.status,
            'overall_assessment': self.overall_assessment,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class InterviewQuestion(Base):
    """Generated interview questions"""
    __tablename__ = 'interview_questions'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    question_type = Column(String(50))  # technical, behavioral, experience
    question = Column(Text, nullable=False)
    expected_answer_guide = Column(Text)
    difficulty = Column(String(20))  # easy, medium, hard
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship('Resume', back_populates='interview_questions')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'question_type': self.question_type,
            'question': self.question,
            'expected_answer_guide': self.expected_answer_guide,
            'difficulty': self.difficulty,
            'order_index': self.order_index
        }


class CandidateNote(Base):
    """Notes about candidates"""
    __tablename__ = 'candidate_notes'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship('Candidate', back_populates='notes')
    author = relationship('User', back_populates='notes')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'note_text': self.note_text,
            'author': self.author.username if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(Base):
    """System configuration"""
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    """API Keys management"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    service = Column(String(50))  # openai, gemini, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'service': self.service,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }


class AuditLog(Base):
    """Audit log for tracking actions"""
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    table_name = Column(String(50))
    record_id = Column(Integer)
    changes_json = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient querying
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
    )
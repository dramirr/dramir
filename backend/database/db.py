"""
Database initialization and management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from .models import Base
from backend.config import get_config

logger = logging.getLogger(__name__)

# Global session factory
SessionLocal = None
engine = None


def init_database(config_class=None):
    """Initialize database connection and create tables"""
    global SessionLocal, engine
    
    if config_class is None:
        config_class = get_config()
    
    # Create engine
    connect_args = {}
    if 'sqlite' in config_class.DATABASE_URL:
        connect_args = {'check_same_thread': False}
        
        # For in-memory databases, use StaticPool
        if ':memory:' in config_class.DATABASE_URL:
            connect_args['poolclass'] = StaticPool
    
    engine = create_engine(
        config_class.DATABASE_URL,
        echo=config_class.DATABASE_ECHO,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    
    # Create session factory
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    SessionLocal = scoped_session(session_factory)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info(f"✅ Database initialized: {config_class.DATABASE_URL}")
    
    return engine, SessionLocal


def get_db():
    """Get database session (for dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_default_admin():
    """Create default admin user if not exists"""
    from .models import User
    
    with get_db_session() as db:
        admin = db.query(User).filter_by(username='admin').first()
        
        if not admin:
            admin = User(
                username='admin',
                email='admin@talentdatar.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')  # Change in production!
            db.add(admin)
            db.commit()
            
            logger.info("✅ Default admin user created (username: admin, password: admin123)")
            logger.warning("⚠️  CHANGE DEFAULT PASSWORD IN PRODUCTION!")
        else:
            logger.info("ℹ️  Admin user already exists")


def seed_database():
    """Seed database with initial data for four positions"""
    from .models import Position, Criterion
    
    with get_db_session() as db:
        position_count = db.query(Position).count()
        
        if position_count == 0:
            # ===== POSITION 1: سرپرست حسابداری (Senior Accountant Supervisor) =====
            position1 = Position(
                title='Senior Accountant Supervisor',
                description='Senior Accounting Supervisor position with financial expertise and team management - Baghdad',
                threshold_percentage=75,
                is_active=True,
                created_by=1
            )
            db.add(position1)
            db.flush()
            
            criteria_list_1 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 20, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 10, 'max': 999, 'score_multiplier': 1.0, 'label': 'Expert'}, {'min': 5, 'max': 9, 'score_multiplier': 0.85, 'label': 'Senior'}, {'min': 2, 'max': 4, 'score_multiplier': 0.5, 'label': 'Qualified'}, {'min': 0, 'max': 1, 'score_multiplier': 0.15, 'label': 'Junior'}], 'unit': 'years', 'description': 'Minimum 2 years required'}, 'display_order': 1},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 15, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.7, 'Associate': 0.3, 'High School': 0.0}, 'min_required': 'Bachelors', 'description': 'Bachelors or higher required'}, 'display_order': 2},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Accounting', 'Finance', 'Financial', 'Audit', 'Economics'], 'match_type': 'any', 'description': 'All finance-related fields accepted'}, 'display_order': 3},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 15, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Supervisor': 0.8, 'Specialist': 0.3}, 'min_required': 'Supervisor', 'description': 'Minimum supervisor level or higher'}, 'display_order': 4},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 13, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Supervisor', 'Manager', 'Senior', 'Lead', 'Head'], 'match_type': 'any', 'description': 'Minimum supervisor level or higher'}, 'display_order': 5},
                {'criterion_key': 'sepidar_skill', 'criterion_name': 'Sepidar Software Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.65, 'Basic': 0.2, 'None': 0.0}, 'min_required': 'Intermediate', 'description': 'Intermediate or higher'}, 'display_order': 6},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Trading', 'Financial', 'Import', 'Export', 'Commercial'], 'match_type': 'any', 'description': 'Trading/financial industries preferred'}, 'display_order': 7},
                {'criterion_key': 'excel_skill', 'criterion_name': 'Microsoft Excel Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 7, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.65, 'Basic': 0.2, 'None': 0.0}, 'min_required': 'Intermediate', 'description': 'Intermediate or higher'}, 'display_order': 8},
                {'criterion_key': 'office_skill', 'criterion_name': 'Office Suite Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 5, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.65, 'Basic': 0.2, 'None': 0.0}, 'min_required': 'Intermediate', 'description': 'Intermediate or higher'}, 'display_order': 9},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'ranged_number', 'weight': 5, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 70, 'max': 100, 'score_multiplier': 1.0, 'label': 'Fluent'}, {'min': 50, 'max': 69, 'score_multiplier': 0.8, 'label': 'Advanced'}, {'min': 30, 'max': 49, 'score_multiplier': 0.5, 'label': 'Intermediate'}, {'min': 0, 'max': 29, 'score_multiplier': 0.0, 'label': 'Basic'}], 'unit': 'percentage', 'description': 'Above 30-40% preferred'}, 'display_order': 10},
                {'criterion_key': 'age', 'criterion_name': 'Age', 'category': 'core', 'data_type': 'ranged_number', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 28, 'max': 40, 'score_multiplier': 1.0, 'label': 'Optimal'}, {'min': 23, 'max': 27, 'score_multiplier': 0.7, 'label': 'Young'}, {'min': 41, 'max': 45, 'score_multiplier': 0.7, 'label': 'Experienced'}, {'min': 0, 'max': 22, 'score_multiplier': 0.2, 'label': 'Too Young'}, {'min': 46, 'max': 999, 'score_multiplier': 0.2, 'label': 'Senior'}], 'unit': 'years', 'description': 'Optimal range: 23-45 years'}, 'display_order': 11},
                {'criterion_key': 'financial_reports_experience', 'criterion_name': 'Financial Reports Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Yes (bonus points)'}, 'display_order': 12},
                {'criterion_key': 'cost_calculation_experience', 'criterion_name': 'Cost Calculation Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Yes (bonus points)'}, 'display_order': 13},
                {'criterion_key': 'warehouse_experience', 'criterion_name': 'Warehouse Operations Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Yes (bonus points)'}, 'display_order': 14},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0, 'label': 'Very Stable'}, {'min': 12, 'max': 23, 'score_multiplier': 0.8, 'label': 'Stable'}, {'min': 8, 'max': 11, 'score_multiplier': 0.5, 'label': 'Moderate'}, {'min': 0, 'max': 7, 'score_multiplier': 0.0, 'label': 'Unstable'}], 'unit': 'months', 'description': 'Minimum 8 months'}, 'display_order': 15},
                {'criterion_key': 'city', 'criterion_name': 'Location (Baghdad)', 'category': 'supplementary', 'data_type': 'text_match', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Baghdad'], 'match_type': 'any', 'description': 'Baghdad preferred'}, 'display_order': 16},
                {'criterion_key': 'organization_type', 'criterion_name': 'Organization Type', 'category': 'supplementary', 'data_type': 'text_match', 'weight': 1, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Trading', 'Commercial'], 'match_type': 'any', 'description': 'Trading companies (bonus)'}, 'display_order': 17}
            ]
            
            for criteria_data in criteria_list_1:
                db.add(Criterion(position_id=position1.id, **criteria_data))
            
            logger.info("✅ Position 1: Senior Accountant Supervisor (17 criteria, max 108 pts)")
            
            # ===== POSITION 2: کارشناس بازرگانی خارجی =====
            position2 = Position(
                title='Foreign Trade Specialist',
                description='International trade and export-import specialist - Baghdad',
                threshold_percentage=75,
                is_active=True,
                created_by=1
            )
            db.add(position2)
            db.flush()
            
            criteria_list_2 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 18, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 5, 'max': 999, 'score_multiplier': 1.0, 'label': 'Expert'}, {'min': 3, 'max': 4, 'score_multiplier': 0.85, 'label': 'Senior'}, {'min': 1, 'max': 2, 'score_multiplier': 0.6, 'label': 'Qualified'}, {'min': 0, 'max': 0, 'score_multiplier': 0.2, 'label': 'Beginner'}], 'unit': 'years', 'description': 'Min 1-2 years required'}, 'display_order': 1},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.7, 'Associate': 0.3, 'High School': 0.0}, 'min_required': 'Bachelors'}, 'display_order': 2},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Business', 'Commerce', 'International Business', 'Trade', 'MBA', 'Management'], 'match_type': 'any'}, 'display_order': 3},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'ranged_number', 'weight': 25, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 90, 'max': 100, 'score_multiplier': 1.0, 'label': 'Native/Fluent'}, {'min': 70, 'max': 89, 'score_multiplier': 0.85, 'label': 'Proficient'}, {'min': 50, 'max': 69, 'score_multiplier': 0.5, 'label': 'Advanced'}, {'min': 30, 'max': 49, 'score_multiplier': 0.2, 'label': 'Intermediate'}, {'min': 0, 'max': 29, 'score_multiplier': 0.0, 'label': 'Basic'}], 'unit': '%', 'min_required': 70}, 'display_order': 4},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Foreign Trade Specialist', 'Trade Specialist', 'Export Specialist', 'Import Specialist', 'International Sales'], 'match_type': 'any'}, 'display_order': 5},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['International Trade', 'Export', 'Import', 'Foreign Trade', 'International Commerce', 'Global Logistics'], 'match_type': 'any'}, 'display_order': 6},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Supervisor': 0.85, 'Senior Specialist': 0.85, 'Specialist': 0.7, 'Junior Specialist': 0.4}}, 'display_order': 7},
                {'criterion_key': 'correspondence_skill', 'criterion_name': 'International Business Correspondence', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 8},
                {'criterion_key': 'shipping_process_knowledge', 'criterion_name': 'Shipping and Logistics Knowledge', 'category': 'core', 'data_type': 'boolean', 'weight': 7, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 9},
                {'criterion_key': 'international_communication', 'criterion_name': 'International Client Communication', 'category': 'core', 'data_type': 'boolean', 'weight': 7, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 10},
                {'criterion_key': 'office_skill', 'criterion_name': 'Office Suite Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 6, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.4, 'None': 0.0}}, 'display_order': 11},
                {'criterion_key': 'age', 'criterion_name': 'Age', 'category': 'core', 'data_type': 'ranged_number', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 25, 'max': 32, 'score_multiplier': 1.0, 'label': 'Optimal'}, {'min': 22, 'max': 24, 'score_multiplier': 0.7, 'label': 'Young'}, {'min': 33, 'max': 35, 'score_multiplier': 0.7, 'label': 'Experienced'}, {'min': 18, 'max': 21, 'score_multiplier': 0.3, 'label': 'Too Young'}, {'min': 36, 'max': 999, 'score_multiplier': 0.3, 'label': 'Out of Range'}], 'unit': 'years'}, 'display_order': 12},
                {'criterion_key': 'market_analysis_skill', 'criterion_name': 'Market Analysis Skill', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 13},
                {'criterion_key': 'negotiation_skill', 'criterion_name': 'Negotiation Skill', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 14},
                {'criterion_key': 'teamwork_experience', 'criterion_name': 'Teamwork Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 15},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0}, {'min': 12, 'max': 23, 'score_multiplier': 0.8}, {'min': 8, 'max': 11, 'score_multiplier': 0.5}, {'min': 0, 'max': 7, 'score_multiplier': 0.0}], 'unit': 'months'}, 'display_order': 16},
                {'criterion_key': 'city', 'criterion_name': 'Location (Baghdad)', 'category': 'supplementary', 'data_type': 'text_match', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Baghdad'], 'match_type': 'any'}, 'display_order': 17},
                {'criterion_key': 'personality_traits', 'criterion_name': 'Personality Traits', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 18}
            ]
            
            for criteria_data in criteria_list_2:
                db.add(Criterion(position_id=position2.id, **criteria_data))
            
            logger.info("✅ Position 2: Foreign Trade Specialist (18 criteria, max 137 pts)")
            
            # ===== POSITION 3: کارشناس توسعه منابع انسانی =====
            position3 = Position(
                title='HR Development Specialist',
                description='Human Resources Development and Training Specialist - Baghdad',
                threshold_percentage=75,
                is_active=True,
                created_by=1
            )
            db.add(position3)
            db.flush()
            
            criteria_list_3 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 20, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 6, 'max': 999, 'score_multiplier': 1.0}, {'min': 4, 'max': 5, 'score_multiplier': 0.85}, {'min': 2, 'max': 3, 'score_multiplier': 0.65}, {'min': 1, 'max': 1, 'score_multiplier': 0.3}, {'min': 0, 'max': 0, 'score_multiplier': 0.0}], 'unit': 'years'}, 'display_order': 1},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.7, 'Associate': 0.3, 'High School': 0.0}}, 'display_order': 2},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Human Resources', 'HRM', 'Business Management', 'Psychology', 'Industrial Psychology', 'Organizational Psychology', 'Management'], 'match_type': 'any'}, 'display_order': 3},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['HR Specialist', 'HR Officer', 'Learning and Development Specialist', 'Training Specialist', 'HR Development'], 'match_type': 'any'}, 'display_order': 4},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Medium Company', 'Large Company', 'Structured Organization'], 'match_type': 'any'}, 'display_order': 5},
                {'criterion_key': 'recruitment_process', 'criterion_name': 'Recruitment and Hiring Process', 'category': 'core', 'data_type': 'boolean', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 6},
                {'criterion_key': 'job_description_skill', 'criterion_name': 'Job Description Development', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 7},
                {'criterion_key': 'hr_analytics', 'criterion_name': 'HR Analytics and Metrics', 'category': 'core', 'data_type': 'boolean', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 8},
                {'criterion_key': 'training_programs', 'criterion_name': 'Training Program Design and Implementation', 'category': 'core', 'data_type': 'boolean', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 9},
                {'criterion_key': 'kpi_design', 'criterion_name': 'KPI Design and Performance Metrics', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 10},
                {'criterion_key': 'hrm_software', 'criterion_name': 'HR Management Software', 'category': 'core', 'data_type': 'graded_category', 'weight': 7, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.65, 'Basic': 0.2, 'None': 0.0}}, 'display_order': 11},
                {'criterion_key': 'office_skill', 'criterion_name': 'Office Suite Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 6, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3, 'None': 0.0}}, 'display_order': 12},
                {'criterion_key': 'communication_counseling', 'criterion_name': 'Communication and Counseling Skills', 'category': 'core', 'data_type': 'boolean', 'weight': 7, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 13},
                {'criterion_key': 'organizational_culture', 'criterion_name': 'Organizational Culture Development', 'category': 'core', 'data_type': 'boolean', 'weight': 6, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 14},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'supplementary', 'data_type': 'graded_category', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Senior Specialist': 0.85, 'Specialist': 0.7, 'Junior Specialist': 0.4}}, 'display_order': 15},
                {'criterion_key': 'teamwork_cross_functional', 'criterion_name': 'Cross-Functional Teamwork', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 16},
                {'criterion_key': 'personality_traits', 'criterion_name': 'Personality Traits', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 17},
                {'criterion_key': 'development_passion', 'criterion_name': 'Passion for Employee Development', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 18},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0}, {'min': 12, 'max': 23, 'score_multiplier': 0.8}, {'min': 8, 'max': 11, 'score_multiplier': 0.5}, {'min': 0, 'max': 7, 'score_multiplier': 0.0}], 'unit': 'months'}, 'display_order': 19},
                {'criterion_key': 'city', 'criterion_name': 'Location (Baghdad)', 'category': 'supplementary', 'data_type': 'text_match', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Baghdad'], 'match_type': 'any'}, 'display_order': 20}
            ]
            
            for criteria_data in criteria_list_3:
                db.add(Criterion(position_id=position3.id, **criteria_data))
            
            logger.info("✅ Position 3: HR Development Specialist (20 criteria, max 145 pts)")
            
            # ===== POSITION 4: کارشناس ارشد بازرگانی خارجی (Senior Foreign Trade Specialist) =====
            position4 = Position(
                title='Senior Foreign Trade Specialist',
                description='Senior specialist in international trade with extensive export-import experience - Baghdad',
                threshold_percentage=75,
                is_active=True,
                created_by=1
            )
            db.add(position4)
            db.flush()
            
            criteria_list_4 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 20, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 7, 'max': 999, 'score_multiplier': 1.0, 'label': 'Expert (7+ years)'}, {'min': 5, 'max': 6, 'score_multiplier': 0.9, 'label': 'Senior (5-6 years)'}, {'min': 3, 'max': 4, 'score_multiplier': 0.7, 'label': 'Qualified (3-4 years)'}, {'min': 1, 'max': 2, 'score_multiplier': 0.3, 'label': 'Beginner (1-2 years)'}, {'min': 0, 'max': 0, 'score_multiplier': 0.0, 'label': 'None'}], 'unit': 'years', 'min_required': 3, 'description': 'Minimum 3 years in foreign trade required'}, 'display_order': 1},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'ranged_number', 'weight': 25, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 90, 'max': 100, 'score_multiplier': 1.0, 'label': 'Fluent/Native (90-100%)'}, {'min': 80, 'max': 89, 'score_multiplier': 0.9, 'label': 'Full Proficiency (80-89%)'}, {'min': 70, 'max': 79, 'score_multiplier': 0.7, 'label': 'Advanced (70-79%)'}, {'min': 50, 'max': 69, 'score_multiplier': 0.4, 'label': 'Intermediate (50-69%)'}, {'min': 0, 'max': 49, 'score_multiplier': 0.0, 'label': 'Weak (0-49%)'}], 'unit': '%', 'min_required': 80, 'description': 'Full proficiency required - minimum 80%'}, 'display_order': 2},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.7, 'Associate': 0.3, 'High School': 0.0}, 'min_required': 'Bachelors'}, 'display_order': 3},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['International Business', 'Business Management', 'Commerce', 'Trade', 'International Trade', 'MBA', 'Management'], 'match_type': 'any', 'description': 'Related fields preferred'}, 'display_order': 4},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Senior Foreign Trade Specialist', 'Senior International Trade Specialist', 'Senior Export Specialist', 'Senior Import Specialist', 'Senior Trade', 'Trade Supervisor'], 'match_type': 'any', 'description': 'Senior level foreign trade specialist required'}, 'display_order': 5},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['International Trade', 'Export', 'Import', 'Foreign Trade', 'International Commerce', 'Global Logistics'], 'match_type': 'any', 'description': 'International trading companies required'}, 'display_order': 6},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Supervisor': 0.9, 'Senior Specialist': 0.75, 'Specialist': 0.4, 'Junior Specialist': 0.0}, 'min_required': 'Senior Specialist'}, 'display_order': 7},
                {'criterion_key': 'commercial_correspondence', 'criterion_name': 'Commercial Correspondence and Business Communication', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Required - Mastery of commercial concepts and business letter writing'}, 'display_order': 8},
                {'criterion_key': 'sourcing_skill', 'criterion_name': 'Sourcing and Supplier Management', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Required - Mastery of foreign supplier sourcing'}, 'display_order': 9},
                {'criterion_key': 'logistics_knowledge', 'criterion_name': 'International Shipping and Logistics Knowledge', 'category': 'core', 'data_type': 'boolean', 'weight': 7, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Required - Familiarity with international transport and logistics'}, 'display_order': 10},
                {'criterion_key': 'negotiation_skill', 'criterion_name': 'Business Negotiation Skills', 'category': 'core', 'data_type': 'boolean', 'weight': 7, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Required - Expertise in business negotiations'}, 'display_order': 11},
                {'criterion_key': 'business_software', 'criterion_name': 'Business Software Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 6, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3, 'None': 0.0}, 'min_required': 'Intermediate', 'description': 'Office, CRM, ERP software - Intermediate or higher preferred'}, 'display_order': 12},
                {'criterion_key': 'teamwork_experience', 'criterion_name': 'Team Leadership Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Bonus - Commercial team cooperation experience'}, 'display_order': 13},
                {'criterion_key': 'personality_traits', 'criterion_name': 'Personality Traits', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Bonus - Persistence, patience, punctuality, commitment, organization'}, 'display_order': 14},
                {'criterion_key': 'career_growth_motivation', 'criterion_name': 'Career Growth Motivation', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0, 'description': 'Bonus - Sign of motivation for career advancement'}, 'display_order': 15},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0, 'label': 'Very Stable (24+ months)'}, {'min': 12, 'max': 23, 'score_multiplier': 0.8, 'label': 'Stable (12-23 months)'}, {'min': 8, 'max': 11, 'score_multiplier': 0.5, 'label': 'Moderate (8-11 months)'}, {'min': 0, 'max': 7, 'score_multiplier': 0.0, 'label': 'Unstable (0-7 months)'}], 'unit': 'months', 'min_required': 8}, 'display_order': 16},
                {'criterion_key': 'city', 'criterion_name': 'Location (Baghdad)', 'category': 'supplementary', 'data_type': 'text_match', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Baghdad'], 'match_type': 'any', 'description': 'Baghdad preferred'}, 'display_order': 17}
            ]
            
            for criteria_data in criteria_list_4:
                db.add(Criterion(position_id=position4.id, **criteria_data))
            
            logger.info("✅ Position 4: Senior Foreign Trade Specialist (17 criteria, max 144 pts)")
            
            # ===== POSITION 5: کارشناس حسابداری (Accounting Specialist) =====
            position5 = Position(title='Accounting Specialist', description='Accounting Specialist with financial expertise - Baghdad', threshold_percentage=75, is_active=True, created_by=1)
            db.add(position5)
            db.flush()
            
            criteria_list_5 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 18, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 8, 'max': 999, 'score_multiplier': 1.0}, {'min': 5, 'max': 7, 'score_multiplier': 0.85}, {'min': 2, 'max': 4, 'score_multiplier': 0.5}, {'min': 0, 'max': 1, 'score_multiplier': 0.2}], 'unit': 'years'}, 'display_order': 1},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 14, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.75, 'Associate': 0.3}}, 'display_order': 2},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 13, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Accounting', 'Finance', 'Financial', 'Audit', 'Economics'], 'match_type': 'any'}, 'display_order': 3},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Supervisor': 0.8, 'Senior Specialist': 0.5, 'Specialist': 0.25}}, 'display_order': 4},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 11, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Accountant', 'Accounting Specialist', 'Financial Specialist', 'Auditor'], 'match_type': 'any'}, 'display_order': 5},
                {'criterion_key': 'accounting_software_skill', 'criterion_name': 'Accounting Software Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 12, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3, 'None': 0.0}}, 'display_order': 6},
                {'criterion_key': 'excel_skill', 'criterion_name': 'Excel Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.25, 'None': 0.0}}, 'display_order': 7},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Trading', 'Financial', 'Commercial', 'Manufacturing'], 'match_type': 'any'}, 'display_order': 8},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'ranged_number', 'weight': 6, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 70, 'max': 100, 'score_multiplier': 1.0}, {'min': 50, 'max': 69, 'score_multiplier': 0.8}, {'min': 30, 'max': 49, 'score_multiplier': 0.5}, {'min': 0, 'max': 29, 'score_multiplier': 0.0}], 'unit': '%'}, 'display_order': 9},
                {'criterion_key': 'accounting_standards', 'criterion_name': 'Knowledge of Accounting Standards/IFRS', 'category': 'core', 'data_type': 'boolean', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 10},
                {'criterion_key': 'age', 'criterion_name': 'Age', 'category': 'core', 'data_type': 'ranged_number', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 25, 'max': 40, 'score_multiplier': 1.0}, {'min': 22, 'max': 24, 'score_multiplier': 0.7}, {'min': 41, 'max': 45, 'score_multiplier': 0.7}], 'unit': 'years'}, 'display_order': 11},
                {'criterion_key': 'financial_reports_experience', 'criterion_name': 'Financial Reports Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 12},
                {'criterion_key': 'cost_accounting_experience', 'criterion_name': 'Cost Accounting Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 13},
                {'criterion_key': 'tax_experience', 'criterion_name': 'Tax & Legal Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 14},
                {'criterion_key': 'accounting_knowledge', 'criterion_name': 'Accounting Knowledge & Expertise', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 15},
                {'criterion_key': 'continuous_learning', 'criterion_name': 'Continuous Learning Commitment', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 16},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0}, {'min': 12, 'max': 23, 'score_multiplier': 0.8}, {'min': 8, 'max': 11, 'score_multiplier': 0.5}, {'min': 0, 'max': 7, 'score_multiplier': 0.0}], 'unit': 'months'}, 'display_order': 17}
            ]
            
            for criteria_data in criteria_list_5:
                db.add(Criterion(position_id=position5.id, **criteria_data))
            
            logger.info("✅ Position 5: Accounting Specialist (17 criteria, max 129 pts)")
            
            # ===== POSITION 6: مدیر داخلی (Internal Manager) =====
            position6 = Position(title='Internal Manager', description='Internal Manager with team management responsibilities - Baghdad', threshold_percentage=75, is_active=True, created_by=1)
            db.add(position6)
            db.flush()
            
            criteria_list_6 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 22, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 12, 'max': 999, 'score_multiplier': 1.0}, {'min': 8, 'max': 11, 'score_multiplier': 0.9}, {'min': 5, 'max': 7, 'score_multiplier': 0.7}, {'min': 0, 'max': 4, 'score_multiplier': 0.2}], 'unit': 'years'}, 'display_order': 1},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 16, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.6, 'Associate': 0.2}}, 'display_order': 2},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 14, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Management', 'Business Administration', 'Finance', 'Economics', 'Law'], 'match_type': 'any'}, 'display_order': 3},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 18, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Manager': 1.0, 'Supervisor': 0.75, 'Senior Specialist': 0.4}}, 'display_order': 4},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 16, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Manager', 'Supervisor', 'Director', 'Head'], 'match_type': 'any'}, 'display_order': 5},
                {'criterion_key': 'team_management_experience', 'criterion_name': 'Team Management Experience', 'category': 'core', 'data_type': 'boolean', 'weight': 14, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 6},
                {'criterion_key': 'management_software_skill', 'criterion_name': 'Management Software Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 11, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3}}, 'display_order': 7},
                {'criterion_key': 'excel_powerbi_skill', 'criterion_name': 'Excel & Power BI Proficiency', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3}}, 'display_order': 8},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Experience', 'category': 'core', 'data_type': 'text_match', 'weight': 9, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'preferred_keywords': ['Banking', 'Financial', 'Commercial', 'Trading'], 'match_type': 'any'}, 'display_order': 9},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'ranged_number', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 70, 'max': 100, 'score_multiplier': 1.0}, {'min': 50, 'max': 69, 'score_multiplier': 0.8}], 'unit': '%'}, 'display_order': 10},
                {'criterion_key': 'age', 'criterion_name': 'Age', 'category': 'core', 'data_type': 'ranged_number', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 30, 'max': 50, 'score_multiplier': 1.0}, {'min': 28, 'max': 29, 'score_multiplier': 0.7}, {'min': 51, 'max': 55, 'score_multiplier': 0.7}], 'unit': 'years'}, 'display_order': 11},
                {'criterion_key': 'strategic_planning_experience', 'criterion_name': 'Strategic Planning Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 4, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 12},
                {'criterion_key': 'problem_solving_experience', 'criterion_name': 'Problem Solving Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 13},
                {'criterion_key': 'team_development_experience', 'criterion_name': 'Team Development Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 14},
                {'criterion_key': 'leadership_skills', 'criterion_name': 'Leadership Skills', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 15},
                {'criterion_key': 'budget_management', 'criterion_name': 'Budget Management Experience', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 16},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0}, {'min': 12, 'max': 23, 'score_multiplier': 0.8}], 'unit': 'months'}, 'display_order': 17}
            ]
            
            for criteria_data in criteria_list_6:
                db.add(Criterion(position_id=position6.id, **criteria_data))
            
            logger.info("✅ Position 6: Internal Manager (17 criteria, max 157.5 pts)")
            
            # ===== POSITION 7: مسئول هماهنگی تیم دیجیتال مارکتینگ (Digital Marketing Team Coordinator) =====
            position7 = Position(title='Digital Marketing Team Coordinator', description='Team coordinator for digital marketing initiatives - Baghdad', threshold_percentage=75, is_active=True, created_by=1)
            db.add(position7)
            db.flush()
            
            criteria_list_7 = [
                {'criterion_key': 'work_experience_years', 'criterion_name': 'Years of Relevant Experience', 'category': 'core', 'data_type': 'ranged_number', 'weight': 18, 'is_required': True, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 4, 'max': 999, 'score_multiplier': 1.0}, {'min': 2, 'max': 3, 'score_multiplier': 0.85}, {'min': 1, 'max': 1, 'score_multiplier': 0.5}, {'min': 0, 'max': 0, 'score_multiplier': 0.1}], 'unit': 'years'}, 'display_order': 1},
                {'criterion_key': 'last_job_title', 'criterion_name': 'Last Job Title', 'category': 'core', 'data_type': 'text_match', 'weight': 15, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Coordinator', 'Assistant', 'Specialist', 'Supervisor'], 'match_type': 'any'}, 'display_order': 2},
                {'criterion_key': 'industry_type', 'criterion_name': 'Industry Type - Digital Marketing', 'category': 'core', 'data_type': 'text_match', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': ['Digital Marketing', 'Marketing', 'Business Development', 'e-commerce'], 'match_type': 'any'}, 'display_order': 3},
                {'criterion_key': 'education_level', 'criterion_name': 'Education Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'categorical', 'levels': {'Doctorate': 1.0, 'Masters': 0.9, 'Bachelors': 0.75, 'Associate': 0.3}}, 'display_order': 4},
                {'criterion_key': 'education_field', 'criterion_name': 'Field of Study', 'category': 'core', 'data_type': 'text_match', 'weight': 3, 'is_required': False, 'config_json': {'scoring_type': 'keyword_match', 'required_keywords': [], 'match_type': 'any'}, 'display_order': 5},
                {'criterion_key': 'communication_skills', 'criterion_name': 'Communication & Team Skills', 'category': 'core', 'data_type': 'boolean', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 6},
                {'criterion_key': 'project_management', 'criterion_name': 'Project Planning & Management', 'category': 'core', 'data_type': 'boolean', 'weight': 12, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 7},
                {'criterion_key': 'process_organization', 'criterion_name': 'Process Organization & Deadline Management', 'category': 'core', 'data_type': 'boolean', 'weight': 10, 'is_required': True, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 8},
                {'criterion_key': 'digital_tools', 'criterion_name': 'Digital Marketing Tools Knowledge', 'category': 'core', 'data_type': 'graded_category', 'weight': 10, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3, 'None': 0.0}}, 'display_order': 9},
                {'criterion_key': 'english_level', 'criterion_name': 'English Language Level', 'category': 'core', 'data_type': 'graded_category', 'weight': 8, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Advanced': 1.0, 'Intermediate': 0.7, 'Basic': 0.3}}, 'display_order': 10},
                {'criterion_key': 'responsibility_level', 'criterion_name': 'Level of Responsibility', 'category': 'core', 'data_type': 'graded_category', 'weight': 5, 'is_required': False, 'config_json': {'scoring_type': 'categorical', 'levels': {'Supervisor': 1.0, 'Lead': 0.8, 'Specialist': 0.5, 'Junior': 0.2}}, 'display_order': 11},
                {'criterion_key': 'digital_marketing_teamwork', 'criterion_name': 'Digital Marketing Team Cooperation', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 12},
                {'criterion_key': 'personality_traits', 'criterion_name': 'Personality Traits - Active, Energetic', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2.5, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 13},
                {'criterion_key': 'career_growth_motivation', 'criterion_name': 'Career Growth Motivation', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 14},
                {'criterion_key': 'problem_solving_skills', 'criterion_name': 'Problem Solving Skills', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 15},
                {'criterion_key': 'time_management', 'criterion_name': 'Time Management Skills', 'category': 'supplementary', 'data_type': 'boolean', 'weight': 2, 'is_required': False, 'config_json': {'scoring_type': 'binary', 'true_value': 1.0, 'false_value': 0.0}, 'display_order': 16},
                {'criterion_key': 'job_stability_months', 'criterion_name': 'Job Stability', 'category': 'supplementary', 'data_type': 'ranged_number', 'weight': 1.5, 'is_required': False, 'config_json': {'scoring_type': 'ranged', 'ranges': [{'min': 24, 'max': 999, 'score_multiplier': 1.0}, {'min': 12, 'max': 23, 'score_multiplier': 0.8}], 'unit': 'months'}, 'display_order': 17}
            ]
            
            for criteria_data in criteria_list_7:
                db.add(Criterion(position_id=position7.id, **criteria_data))
            
            logger.info("✅ Position 7: Digital Marketing Team Coordinator (17 criteria, max 127.5 pts)")
            
            db.commit()
            logger.info("\n" + "="*80)
            logger.info("✅ ALL 7 POSITIONS SEEDED SUCCESSFULLY!")
            logger.info("="*80)
            logger.info("📊 POSITIONS SUMMARY:")
            logger.info("  1. Senior Accountant Supervisor         - 17 criteria, Max: 108 pts (75% = 81 pts)")
            logger.info("  2. Foreign Trade Specialist            - 18 criteria, Max: 137 pts (75% = 102.75 pts)")
            logger.info("  3. HR Development Specialist           - 20 criteria, Max: 145 pts (75% = 108.75 pts)")
            logger.info("  4. Senior Foreign Trade Specialist     - 17 criteria, Max: 144 pts (75% = 108 pts)")
            logger.info("  5. Accounting Specialist               - 17 criteria, Max: 129 pts (75% = 96.75 pts)")
            logger.info("  6. Internal Manager                    - 17 criteria, Max: 157.5 pts (75% = 118.13 pts)")
            logger.info("  7. Digital Marketing Team Coordinator  - 17 criteria, Max: 127.5 pts (75% = 95.63 pts)")
            logger.info("="*80 + "\n")
        else:
            logger.info("ℹ️  Database already has positions")


def reset_database():
    """Drop all tables and recreate (for development only!)"""
    global engine
    
    if engine is None:
        logger.error("❌ Database not initialized")
        return
    
    logger.warning("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    logger.info("✅ Recreating tables...")
    Base.metadata.create_all(bind=engine)
    
    logger.info("✅ Database reset complete")
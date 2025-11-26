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
    """Seed database with initial data"""
    from .models import Position, Criterion, SystemConfig
    import json
    
    with get_db_session() as db:
        position_count = db.query(Position).count()
        
        if position_count == 0:
            # پوزیشن 1: سرپرست حسابداری (همان JSON اولیه شما)
            position1 = Position(
                title='Senior Accountant Supervisor',
                description='Senior Accounting Supervisor position with financial expertise and team management',
                threshold_percentage=75,
                is_active=True,
                created_by=1
            )
            db.add(position1)
            db.flush()
            
            # Criteria برای پوزیشن 1
            criteria_list_1 = [
                {
                    'criterion_key': 'work_experience_years',
                    'criterion_name': 'Years of Relevant Experience',
                    'category': 'core',
                    'data_type': 'ranged_number',
                    'weight': 20,
                    'is_required': True,
                    'config_json': {
                        'scoring_type': 'ranged',
                        'ranges': [
                            {'min': 10, 'max': 999, 'score_multiplier': 1.0, 'label': 'Expert'},
                            {'min': 5, 'max': 9, 'score_multiplier': 0.85, 'label': 'Senior'},
                            {'min': 2, 'max': 4, 'score_multiplier': 0.6, 'label': 'Qualified'},
                            {'min': 0, 'max': 1, 'score_multiplier': 0.15, 'label': 'Junior'}
                        ],
                        'unit': 'years',
                        'description': 'حداقل ۲ سال سابقه'
                    },
                    'display_order': 1
                },
                {
                    'criterion_key': 'education_level',
                    'criterion_name': 'Education Level',
                    'category': 'core',
                    'data_type': 'graded_category',
                    'weight': 15,
                    'is_required': True,
                    'config_json': {
                        'scoring_type': 'categorical',
                        'levels': {
                            'Doctorate': 1.0,
                            'Masters': 0.9,
                            'Bachelors': 0.7,
                            'Associate': 0.3,
                            'High School': 0.0
                        },
                        'min_required': 'Bachelors',
                        'description': 'کارشناسی یا بالاتر الزامی'
                    },
                    'display_order': 2
                },
                {
                    'criterion_key': 'education_field',
                    'criterion_name': 'Field of Study',
                    'category': 'core',
                    'data_type': 'text_match',
                    'weight': 10,
                    'is_required': True,
                    'config_json': {
                        'scoring_type': 'keyword_match',
                        'required_keywords': ['Accounting', 'Finance', 'Financial', 'حسابداری', 'مالی'],
                        'match_type': 'any',
                        'description': 'تمام رشته های مالی'
                    },
                    'display_order': 3
                },
                {
                    'criterion_key': 'responsibility_level',
                    'criterion_name': 'Level of Responsibility',
                    'category': 'core',
                    'data_type': 'graded_category',
                    'weight': 15,
                    'is_required': True,
                    'config_json': {
                        'scoring_type': 'categorical',
                        'levels': {
                            'Manager': 1.0,
                            'Supervisor': 0.8,
                            'Specialist': 0.3
                        },
                        'min_required': 'Supervisor',
                        'description': 'حداقل دارای سمت سرپرست به بالا'
                    },
                    'display_order': 4
                },
                {
                    'criterion_key': 'last_job_title',
                    'criterion_name': 'Last Job Title',
                    'category': 'core',
                    'data_type': 'text_match',
                    'weight': 15,
                    'is_required': True,
                    'config_json': {
                        'scoring_type': 'keyword_match',
                        'required_keywords': ['Supervisor', 'Manager', 'Senior', 'Lead'],
                        'match_type': 'any',
                        'description': 'حداقل دارای سمت سرپرست به بالا'
                    },
                    'display_order': 5
                },
                {
                    'criterion_key': 'sepidar_skill',
                    'criterion_name': 'Sepidar Software Proficiency',
                    'category': 'core',
                    'data_type': 'graded_category',
                    'weight': 10,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'categorical',
                        'levels': {
                            'Advanced': 1.0,
                            'Intermediate': 0.65,
                            'Basic': 0.2,
                            'None': 0.0
                        },
                        'min_required': 'Intermediate',
                        'description': 'متوسط به بالا (نرم افزار های سپیدار / همکاران / راهکاران)'
                    },
                    'display_order': 6
                },
                {
                    'criterion_key': 'industry_type',
                    'criterion_name': 'Industry Experience',
                    'category': 'core',
                    'data_type': 'text_match',
                    'weight': 10,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'keyword_match',
                        'preferred_keywords': ['Trading', 'Financial', 'Import', 'Export', 'بازرگانی', 'مالی', 'صادرات', 'واردات'],
                        'match_type': 'any',
                        'description': 'صنایع بازرگانی، مالی یا صادرات و واردات ترجیح دارد'
                    },
                    'display_order': 7
                },
                {
                    'criterion_key': 'excel_skill',
                    'criterion_name': 'Microsoft Excel Proficiency',
                    'category': 'core',
                    'data_type': 'graded_category',
                    'weight': 8,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'categorical',
                        'levels': {
                            'Advanced': 1.0,
                            'Intermediate': 0.65,
                            'Basic': 0.2,
                            'None': 0.0
                        },
                        'min_required': 'Intermediate',
                        'description': 'متوسط به بالا'
                    },
                    'display_order': 8
                },
                {
                    'criterion_key': 'english_level',
                    'criterion_name': 'English Language Level',
                    'category': 'core',
                    'data_type': 'ranged_number',
                    'weight': 5,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'ranged',
                        'ranges': [
                            {'min': 70, 'max': 100, 'score_multiplier': 1.0, 'label': 'Fluent'},
                            {'min': 50, 'max': 69, 'score_multiplier': 0.8, 'label': 'Advanced'},
                            {'min': 30, 'max': 49, 'score_multiplier': 0.5, 'label': 'Intermediate'},
                            {'min': 0, 'max': 29, 'score_multiplier': 0.0, 'label': 'Basic'}
                        ],
                        'unit': 'percentage',
                        'min_required': 30,
                        'description': 'بالا تر از 30 - 40 درصد'
                    },
                    'display_order': 9
                },
                {
                    'criterion_key': 'office_skill',
                    'criterion_name': 'Office Suite Proficiency',
                    'category': 'core',
                    'data_type': 'graded_category',
                    'weight': 5,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'categorical',
                        'levels': {
                            'Advanced': 1.0,
                            'Intermediate': 0.65,
                            'Basic': 0.2,
                            'None': 0.0
                        },
                        'min_required': 'Intermediate',
                        'description': 'متوسط به بالا'
                    },
                    'display_order': 10
                },
                {
                    'criterion_key': 'age',
                    'criterion_name': 'Age',
                    'category': 'core',
                    'data_type': 'ranged_number',
                    'weight': 3,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'ranged',
                        'ranges': [
                            {'min': 28, 'max': 40, 'score_multiplier': 1.0, 'label': 'Optimal'},
                            {'min': 23, 'max': 27, 'score_multiplier': 0.7, 'label': 'Young'},
                            {'min': 41, 'max': 45, 'score_multiplier': 0.7, 'label': 'Experienced'},
                            {'min': 0, 'max': 22, 'score_multiplier': 0.2, 'label': 'Too Young'},
                            {'min': 46, 'max': 999, 'score_multiplier': 0.2, 'label': 'Senior'}
                        ],
                        'unit': 'years',
                        'description': 'محدوده مطلوب: 23 تا 45 سال'
                    },
                    'display_order': 11
                },
                # Supplementary criteria
                {
                    'criterion_key': 'financial_reports_experience',
                    'criterion_name': 'Financial Reports Experience',
                    'category': 'supplementary',
                    'data_type': 'boolean',
                    'weight': 2,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'binary',
                        'true_value': 1.0,
                        'false_value': 0.0,
                        'description': 'بله (امتیازی)'
                    },
                    'display_order': 12
                },
                {
                    'criterion_key': 'cost_calculation_experience',
                    'criterion_name': 'Cost Calculation Experience',
                    'category': 'supplementary',
                    'data_type': 'boolean',
                    'weight': 2,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'binary',
                        'true_value': 1.0,
                        'false_value': 0.0,
                        'description': 'بله (امتیازی)'
                    },
                    'display_order': 13
                },
                {
                    'criterion_key': 'job_stability_months',
                    'criterion_name': 'Job Stability',
                    'category': 'supplementary',
                    'data_type': 'ranged_number',
                    'weight': 2,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'ranged',
                        'ranges': [
                            {'min': 24, 'max': 999, 'score_multiplier': 1.0, 'label': 'Very Stable'},
                            {'min': 12, 'max': 23, 'score_multiplier': 0.8, 'label': 'Stable'},
                            {'min': 8, 'max': 11, 'score_multiplier': 0.5, 'label': 'Moderate'},
                            {'min': 0, 'max': 7, 'score_multiplier': 0.0, 'label': 'Unstable'}
                        ],
                        'unit': 'months',
                        'min_required': 8,
                        'description': 'حداقل 8 ماه'
                    },
                    'display_order': 14
                },
                {
                    'criterion_key': 'city',
                    'criterion_name': 'Location (Baghdad)',
                    'category': 'supplementary',
                    'data_type': 'text_match',
                    'weight': 2,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'keyword_match',
                        'preferred_keywords': ['Baghdad', 'بغداد'],
                        'match_type': 'any',
                        'description': 'بغداد'
                    },
                    'display_order': 15
                },
                {
                    'criterion_key': 'organization_type',
                    'criterion_name': 'Organization Type',
                    'category': 'supplementary',
                    'data_type': 'text_match',
                    'weight': 1,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'keyword_match',
                        'preferred_keywords': ['Trading', 'Commercial', 'بازرگانی'],
                        'match_type': 'any',
                        'description': 'شرکت‌های بازرگانی (امتیازی)'
                    },
                    'display_order': 16
                },
                {
                    'criterion_key': 'warehouse_experience',
                    'criterion_name': 'Warehouse Operations Experience',
                    'category': 'supplementary',
                    'data_type': 'boolean',
                    'weight': 1,
                    'is_required': False,
                    'config_json': {
                        'scoring_type': 'binary',
                        'true_value': 1.0,
                        'false_value': 0.0,
                        'description': 'بله (امتیازی)'
                    },
                    'display_order': 17
                }
            ]
            
            for criteria_data in criteria_list_1:
                criterion = Criterion(
                    position_id=position1.id,
                    **criteria_data
                )
                db.add(criterion)
            
            logger.info("✅ Position 1 created: Senior Accountant Supervisor")
            
            # اگر می‌خواهید پوزیشن‌های بیشتری اضافه کنید، اینجا ادامه دهید
            
            db.commit()
            logger.info("✅ Default positions and criteria seeded")
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
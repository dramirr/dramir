from .auth import auth_bp
from .positions import positions_bp
from .criteria import criteria_bp
from .resumes import resumes_bp
from .candidates import candidates_bp

__all__ = [
    'auth_bp',
    'positions_bp',
    'criteria_bp',
    'resumes_bp',
    'candidates_bp'
]
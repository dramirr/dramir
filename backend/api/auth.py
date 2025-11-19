"""
Authentication API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
import logging

from database.db import get_db_session
from database.models import User, AuditLog

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        with get_db_session() as db:
            user = db.query(User).filter_by(username=username).first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent username: {username}")
                return jsonify({'error': 'Invalid credentials'}), 401
            
            if not user.check_password(password):
                logger.warning(f"Failed login attempt for user: {username}")
                return jsonify({'error': 'Invalid credentials'}), 401
            
            if not user.is_active:
                logger.warning(f"Login attempt for inactive user: {username}")
                return jsonify({'error': 'Account is inactive'}), 403
            
            user.last_login = datetime.utcnow()
            
            # CRITICAL: identity must be string
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    'role': user.role,
                    'username': user.username
                }
            )
            
            audit_log = AuditLog(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"User logged in: {username}")
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (admin only in production)"""
    try:
        data = request.json
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'viewer')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        with get_db_session() as db:
            if db.query(User).filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            
            if db.query(User).filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 400
            
            user = User(
                username=username,
                email=email,
                role=role,
                is_active=True
            )
            user.set_password(password)
            
            db.add(user)
            db.flush()
            
            audit_log = AuditLog(
                user_id=None,
                action='register',
                table_name='users',
                record_id=user.id,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"New user registered: {username}")
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        
        with get_db_session() as db:
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify(user.to_dict())
            
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get user info'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        data = request.json
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new password required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        
        with get_db_session() as db:
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.check_password(old_password):
                return jsonify({'error': 'Invalid old password'}), 401
            
            user.set_password(new_password)
            
            audit_log = AuditLog(
                user_id=user_id,
                action='change_password',
                table_name='users',
                record_id=user_id,
                ip_address=request.remote_addr
            )
            db.add(audit_log)
            
            logger.info(f"Password changed for user: {user.username}")
            
            return jsonify({'message': 'Password changed successfully'})
            
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to change password'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        user_id = int(get_jwt_identity())  # Convert string to int
        
        with get_db_session() as db:
            audit_log = AuditLog(
                user_id=user_id,
                action='logout',
                ip_address=request.remote_addr
            )
            db.add(audit_log)
        
        logger.info(f"User logged out: {user_id}")
        
        return jsonify({'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Logout failed'}), 500
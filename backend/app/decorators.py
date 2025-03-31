from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get user ID from token
            user_id = get_jwt_identity()
            
            # Get user from database
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'error': 'User not found'}), 404
                
            # Add user to kwargs
            kwargs['current_user'] = current_user
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Invalid or missing token'}), 401
            
    return decorated 
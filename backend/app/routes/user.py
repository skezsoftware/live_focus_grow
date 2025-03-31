from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()
        
        # Query the user from the database
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Return user profile data
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'level': user.level,
            'current_xp': user.current_xp,
            'streak_days': user.streak_days,
            'multiplier': user.multiplier,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return jsonify({'error': 'Failed to get user profile'}), 500

@user_bp.route('/profile', methods=['PUT', 'PATCH'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        data = request.get_json()
        
        # Update allowed fields
        if 'username' in data:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Username already taken'}), 400
            user.username = data['username']
            
        if 'email' in data:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'level': user.level,
                'current_xp': user.current_xp,
                'streak_days': user.streak_days,
                'multiplier': user.multiplier,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500
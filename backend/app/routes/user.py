from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'level': user.level,
        'current_xp': user.current_xp,
        'streak_days': user.streak_days,
        'multiplier': user.multiplier
    })

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    data = request.get_json()
    
    # Update only allowed fields
    if 'username' in data:
        # Check if username is already taken
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'error': 'Username already taken'}), 400
        user.username = data['username']
    
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
            'multiplier': user.multiplier
        }
    })
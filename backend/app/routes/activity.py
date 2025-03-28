from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Activity, UserActivityLog
from app.extensions import db
import uuid

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    activities = Activity.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'category': a.category,
        'xp_value': a.xp_value,
        'description': a.description
    } for a in activities])

@activity_bp.route('/activities', methods=['POST'])
@jwt_required()
def create_activity():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'category', 'xp_value']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Validate category
    valid_categories = ['Mind', 'Body', 'Life']
    if data['category'] not in valid_categories:
        return jsonify({'error': 'Invalid category. Must be one of: Mind, Body, Life'}), 400
        
    # Validate xp_value
    if not isinstance(data['xp_value'], (int, float)) or data['xp_value'] <= 0:
        return jsonify({'error': 'XP value must be a positive number'}), 400
    
    # Create new activity
    new_activity = Activity(
        id=str(uuid.uuid4()),
        name=data['name'],
        category=data['category'],
        xp_value=float(data['xp_value']),
        description=data.get('description', '')
    )
    
    db.session.add(new_activity)
    db.session.commit()
    
    return jsonify({
        'id': new_activity.id,
        'name': new_activity.name,
        'category': new_activity.category,
        'xp_value': new_activity.xp_value,
        'description': new_activity.description
    }), 201

@activity_bp.route('/activities/<activity_id>', methods=['PUT'])
@jwt_required()
def update_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        activity.name = data['name']
    if 'category' in data:
        if data['category'] not in ['Mind', 'Body', 'Life']:
            return jsonify({'error': 'Invalid category. Must be one of: Mind, Body, Life'}), 400
        activity.category = data['category']
    if 'xp_value' in data:
        if not isinstance(data['xp_value'], (int, float)) or data['xp_value'] <= 0:
            return jsonify({'error': 'XP value must be a positive number'}), 400
        activity.xp_value = float(data['xp_value'])
    if 'description' in data:
        activity.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'id': activity.id,
        'name': activity.name,
        'category': activity.category,
        'xp_value': activity.xp_value,
        'description': activity.description
    })

@activity_bp.route('/activities/<activity_id>', methods=['DELETE'])
@jwt_required()
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    
    # Soft delete by setting is_active to False
    activity.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Activity deactivated successfully'})
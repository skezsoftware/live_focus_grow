from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Activity, UserActivityLog
from app.extensions import db

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
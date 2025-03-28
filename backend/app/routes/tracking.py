from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Journal, WeightLog, ProgressPhoto
from app.extensions import db
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func
import json

tracking_bp = Blueprint('tracking', __name__)

def get_pagination_params():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return page, per_page

# Journal Routes
@tracking_bp.route('/journals', methods=['GET'])
@jwt_required()
def get_journals():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = Journal.query.filter_by(user_id=user_id)
    
    # Apply filters
    mood = request.args.get('mood')
    if mood:
        query = query.filter_by(mood=mood)
    
    start_date = request.args.get('start_date')
    if start_date:
        query = query.filter(Journal.created_at >= datetime.fromisoformat(start_date))
    
    end_date = request.args.get('end_date')
    if end_date:
        query = query.filter(Journal.created_at <= datetime.fromisoformat(end_date))
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'created_at')
    if sort_by in ['created_at', 'title']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(Journal, sort_by)))
        else:
            query = query.order_by(getattr(Journal, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    journals = pagination.items
    
    return jsonify({
        'items': [{
            'id': j.id,
            'title': j.title,
            'content': j.content,
            'mood': j.mood,
            'created_at': j.created_at.isoformat()
        } for j in journals],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@tracking_bp.route('/journals', methods=['POST'])
@jwt_required()
def create_journal():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    
    # Create new journal entry
    new_journal = Journal(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=data.get('title', ''),
        content=data['content'],
        mood=data.get('mood')
    )
    
    db.session.add(new_journal)
    db.session.commit()
    
    return jsonify({
        'id': new_journal.id,
        'title': new_journal.title,
        'content': new_journal.content,
        'mood': new_journal.mood,
        'created_at': new_journal.created_at.isoformat()
    }), 201

@tracking_bp.route('/journals/<journal_id>', methods=['PUT'])
@jwt_required()
def update_journal(journal_id):
    user_id = get_jwt_identity()
    journal = Journal.query.filter_by(id=journal_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'title' in data:
        journal.title = data['title']
    if 'content' in data:
        journal.content = data['content']
    if 'mood' in data:
        journal.mood = data['mood']
    
    db.session.commit()
    
    return jsonify({
        'id': journal.id,
        'title': journal.title,
        'content': journal.content,
        'mood': journal.mood,
        'created_at': journal.created_at.isoformat()
    })

@tracking_bp.route('/journals/<journal_id>', methods=['DELETE'])
@jwt_required()
def delete_journal(journal_id):
    user_id = get_jwt_identity()
    journal = Journal.query.filter_by(id=journal_id, user_id=user_id).first_or_404()
    db.session.delete(journal)
    db.session.commit()
    return jsonify({'message': 'Journal entry deleted successfully'})

# Weight Log Routes
@tracking_bp.route('/weight-logs', methods=['GET'])
@jwt_required()
def get_weight_logs():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = WeightLog.query.filter_by(user_id=user_id)
    
    # Apply filters
    start_date = request.args.get('start_date')
    if start_date:
        query = query.filter(WeightLog.date >= datetime.fromisoformat(start_date))
    
    end_date = request.args.get('end_date')
    if end_date:
        query = query.filter(WeightLog.date <= datetime.fromisoformat(end_date))
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'date')
    if sort_by in ['date', 'weight']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(WeightLog, sort_by)))
        else:
            query = query.order_by(getattr(WeightLog, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    logs = pagination.items
    
    return jsonify({
        'items': [{
            'id': l.id,
            'weight': l.weight,
            'date': l.date.isoformat(),
            'notes': l.notes
        } for l in logs],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@tracking_bp.route('/weight-logs', methods=['POST'])
@jwt_required()
def create_weight_log():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if 'weight' not in data:
        return jsonify({'error': 'Weight is required'}), 400
    
    # Validate weight is positive
    if not isinstance(data['weight'], (int, float)) or data['weight'] <= 0:
        return jsonify({'error': 'Weight must be a positive number'}), 400
    
    # Create new weight log
    new_log = WeightLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        weight=float(data['weight']),
        date=datetime.fromisoformat(data.get('date', datetime.now(timezone.utc).isoformat())),
        notes=data.get('notes', '')
    )
    
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({
        'id': new_log.id,
        'weight': new_log.weight,
        'date': new_log.date.isoformat(),
        'notes': new_log.notes
    }), 201

@tracking_bp.route('/weight-logs/<log_id>', methods=['PUT'])
@jwt_required()
def update_weight_log(log_id):
    user_id = get_jwt_identity()
    log = WeightLog.query.filter_by(id=log_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'weight' in data:
        if not isinstance(data['weight'], (int, float)) or data['weight'] <= 0:
            return jsonify({'error': 'Weight must be a positive number'}), 400
        log.weight = float(data['weight'])
    if 'date' in data:
        log.date = datetime.fromisoformat(data['date'])
    if 'notes' in data:
        log.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'id': log.id,
        'weight': log.weight,
        'date': log.date.isoformat(),
        'notes': log.notes
    })

@tracking_bp.route('/weight-logs/<log_id>', methods=['DELETE'])
@jwt_required()
def delete_weight_log(log_id):
    user_id = get_jwt_identity()
    log = WeightLog.query.filter_by(id=log_id, user_id=user_id).first_or_404()
    db.session.delete(log)
    db.session.commit()
    return jsonify({'message': 'Weight log deleted successfully'})

# Progress Photo Routes
@tracking_bp.route('/progress-photos', methods=['GET'])
@jwt_required()
def get_progress_photos():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = ProgressPhoto.query.filter_by(user_id=user_id)
    
    # Apply filters
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    start_date = request.args.get('start_date')
    if start_date:
        query = query.filter(ProgressPhoto.date >= datetime.fromisoformat(start_date))
    
    end_date = request.args.get('end_date')
    if end_date:
        query = query.filter(ProgressPhoto.date <= datetime.fromisoformat(end_date))
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'date')
    if sort_by in ['date', 'category']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(ProgressPhoto, sort_by)))
        else:
            query = query.order_by(getattr(ProgressPhoto, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    photos = pagination.items
    
    return jsonify({
        'items': [{
            'id': p.id,
            'photo_url': p.photo_url,
            'category': p.category,
            'date': p.date.isoformat(),
            'notes': p.notes
        } for p in photos],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@tracking_bp.route('/progress-photos', methods=['POST'])
@jwt_required()
def create_progress_photo():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['photo_url', 'category']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate category
    valid_categories = ['front', 'side', 'back']
    if data['category'] not in valid_categories:
        return jsonify({'error': 'Invalid category. Must be one of: front, side, back'}), 400
    
    # Create new progress photo
    new_photo = ProgressPhoto(
        id=str(uuid.uuid4()),
        user_id=user_id,
        photo_url=data['photo_url'],
        category=data['category'],
        date=datetime.fromisoformat(data.get('date', datetime.now(timezone.utc).isoformat())),
        notes=data.get('notes', '')
    )
    
    db.session.add(new_photo)
    db.session.commit()
    
    return jsonify({
        'id': new_photo.id,
        'photo_url': new_photo.photo_url,
        'category': new_photo.category,
        'date': new_photo.date.isoformat(),
        'notes': new_photo.notes
    }), 201

@tracking_bp.route('/progress-photos/<photo_id>', methods=['PUT'])
@jwt_required()
def update_progress_photo(photo_id):
    user_id = get_jwt_identity()
    photo = ProgressPhoto.query.filter_by(id=photo_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'photo_url' in data:
        photo.photo_url = data['photo_url']
    if 'category' in data:
        valid_categories = ['front', 'side', 'back']
        if data['category'] not in valid_categories:
            return jsonify({'error': 'Invalid category. Must be one of: front, side, back'}), 400
        photo.category = data['category']
    if 'date' in data:
        photo.date = datetime.fromisoformat(data['date'])
    if 'notes' in data:
        photo.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'id': photo.id,
        'photo_url': photo.photo_url,
        'category': photo.category,
        'date': photo.date.isoformat(),
        'notes': photo.notes
    })

@tracking_bp.route('/progress-photos/<photo_id>', methods=['DELETE'])
@jwt_required()
def delete_progress_photo(photo_id):
    user_id = get_jwt_identity()
    photo = ProgressPhoto.query.filter_by(id=photo_id, user_id=user_id).first_or_404()
    db.session.delete(photo)
    db.session.commit()
    return jsonify({'message': 'Progress photo deleted successfully'})

# Analytics Routes
@tracking_bp.route('/analytics/weight-trend', methods=['GET'])
@jwt_required()
def get_weight_trend():
    user_id = get_jwt_identity()
    
    # Get time period from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    # Get weight logs
    logs = WeightLog.query.filter(
        WeightLog.user_id == user_id,
        WeightLog.date >= start_date
    ).order_by(WeightLog.date).all()
    
    if not logs:
        return jsonify({
            'weight_data': [],
            'start_weight': None,
            'current_weight': None,
            'weight_change': 0,
            'average_weight': 0
        })
    
    # Calculate statistics
    start_weight = logs[0].weight
    current_weight = logs[-1].weight
    weight_change = current_weight - start_weight
    average_weight = sum(log.weight for log in logs) / len(logs)
    
    # Format weight data for chart
    weight_data = [{
        'date': log.date.isoformat(),
        'weight': log.weight
    } for log in logs]
    
    return jsonify({
        'weight_data': weight_data,
        'start_weight': start_weight,
        'current_weight': current_weight,
        'weight_change': weight_change,
        'average_weight': average_weight
    })

@tracking_bp.route('/analytics/mood-trend', methods=['GET'])
@jwt_required()
def get_mood_trend():
    user_id = get_jwt_identity()
    
    # Get time period from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    # Get journal entries with mood
    entries = Journal.query.filter(
        Journal.user_id == user_id,
        Journal.created_at >= start_date,
        Journal.mood.isnot(None)
    ).order_by(Journal.created_at).all()
    
    if not entries:
        return jsonify({
            'mood_data': [],
            'mood_distribution': {},
            'average_mood': None
        })
    
    # Calculate mood distribution
    mood_counts = {}
    for entry in entries:
        mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1
    
    # Format mood data for chart
    mood_data = [{
        'date': entry.created_at.isoformat(),
        'mood': entry.mood
    } for entry in entries]
    
    return jsonify({
        'mood_data': mood_data,
        'mood_distribution': mood_counts,
        'total_entries': len(entries)
    })

@tracking_bp.route('/analytics/progress-summary', methods=['GET'])
@jwt_required()
def get_progress_summary():
    user_id = get_jwt_identity()
    
    # Get time period from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    # Get progress photos by category
    photos = ProgressPhoto.query.filter(
        ProgressPhoto.user_id == user_id,
        ProgressPhoto.date >= start_date
    ).all()
    
    # Group photos by category
    category_photos = {}
    for photo in photos:
        if photo.category not in category_photos:
            category_photos[photo.category] = []
        category_photos[photo.category].append({
            'date': photo.date.isoformat(),
            'photo_url': photo.photo_url
        })
    
    # Get weight logs
    weight_logs = WeightLog.query.filter(
        WeightLog.user_id == user_id,
        WeightLog.date >= start_date
    ).order_by(WeightLog.date).all()
    
    # Calculate weight statistics
    weight_stats = {
        'start_weight': weight_logs[0].weight if weight_logs else None,
        'current_weight': weight_logs[-1].weight if weight_logs else None,
        'weight_change': (weight_logs[-1].weight - weight_logs[0].weight) if weight_logs else 0,
        'total_measurements': len(weight_logs)
    }
    
    return jsonify({
        'category_photos': category_photos,
        'weight_stats': weight_stats,
        'total_photos': len(photos)
    }) 
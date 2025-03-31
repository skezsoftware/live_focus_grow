from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.tracking import Journal, WeightLog, ProgressPhoto
from app.models.activity import Activity, UserActivity
from app.models.user import User
from app.extensions import db
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func
import json
from app.decorators import token_required

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

# Activity Management Routes
@tracking_bp.route('/all-activities', methods=['GET'])
@jwt_required()
def get_all_activities():
    try:
        print("\n=== GET /all-activities ===")
        
        # Define default activities that should always be available
        default_activities = [
            {
                'id': '1',
                'name': 'Weight Lifting',
                'category': 'Mind + Body',
                'type': 'exercise',
                'is_custom': False
            },
            {
                'id': '2',
                'name': 'Reading',
                'category': 'Mind + Body',
                'type': 'learning',
                'is_custom': False
            },
            {
                'id': '3',
                'name': 'Family Activity',
                'category': 'Purpose + People',
                'type': 'social',
                'is_custom': False
            },
            {
                'id': '4',
                'name': 'Learning New Skill',
                'category': 'Growth + Creation',
                'type': 'learning',
                'is_custom': False
            },
            {
                'id': '5',
                'name': 'Boxing',
                'category': 'Mind + Body',
                'type': 'exercise',
                'is_custom': False
            },
            {
                'id': '6',
                'name': 'Meditation',
                'category': 'Mind + Body',
                'type': 'mindfulness',
                'is_custom': False
            },
            {
                'id': '7',
                'name': 'Online Course',
                'category': 'Growth + Creation',
                'type': 'learning',
                'is_custom': False
            },
            {
                'id': '8',
                'name': 'Creative Writing',
                'category': 'Growth + Creation',
                'type': 'creativity',
                'is_custom': False
            },
            {
                'id': '9',
                'name': 'Volunteer Work',
                'category': 'Purpose + People',
                'type': 'social',
                'is_custom': False
            },
            {
                'id': '10',
                'name': 'Mentoring',
                'category': 'Purpose + People',
                'type': 'social',
                'is_custom': False
            }
        ]
        
        # Initialize categorized activities with default activities
        categorized = {
            "Mind + Body": [],
            "Growth + Creation": [],
            "Purpose + People": []
        }
        
        # Add default activities to their categories
        for activity in default_activities:
            if activity['category'] in categorized:
                categorized[activity['category']].append(activity)
        
        # Get custom activities from database
        user_id = get_jwt_identity()
        custom_activities = Activity.query.filter_by(user_id=user_id, is_custom=True).all()
        
        # Add custom activities to the lists
        for activity in custom_activities:
            activity_data = {
                'id': str(activity.id),
                'name': activity.name,
                'category': activity.category,
                'type': activity.type,
                'is_custom': True
            }
            if activity.category in categorized:
                categorized[activity.category].append(activity_data)
                default_activities.append(activity_data)
        
        print("Activities by category:")
        for category, acts in categorized.items():
            print(f"{category}: {len(acts)} activities")
            for act in acts:
                print(f"  - {act['name']} ({act['type']})")
        
        response_data = {
            'activities': default_activities,
            'categorized_activities': categorized
        }
        
        print("Sending response:", response_data)
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error in get_all_activities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    # Redirect to all-activities endpoint to ensure consistency
    return get_all_activities()

@tracking_bp.route('/activities', methods=['POST'])
@jwt_required()
def update_selected_activities():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        activities = data.get('activities', [])
        
        # First, mark all existing activities as inactive
        UserActivity.query.filter_by(user_id=user_id).update({'is_active': False})
        db.session.commit()
        
        # Add new activities
        for activity_data in activities:
            # Check if activity already exists
            existing_activity = UserActivity.query.filter_by(
                user_id=user_id,
                activity_id=activity_data['id']
            ).first()
            
            if existing_activity:
                # Update existing activity
                existing_activity.is_active = True
                existing_activity.activity_name = activity_data['name']
                existing_activity.category = activity_data['category']
                existing_activity.type = activity_data.get('type', 'custom')
            else:
                # Create new activity
                new_activity = UserActivity(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    activity_id=activity_data['id'],
                    activity_name=activity_data['name'],
                    category=activity_data['category'],
                    type=activity_data.get('type', 'custom'),
                    is_active=True
                )
                db.session.add(new_activity)
        
        # Update user's XP
        user = User.query.get(user_id)
        if user:
            user.current_xp += len(activities) * 10  # 10 XP per activity
            new_level = (user.current_xp // 100) + 1
            level_up = new_level > user.level
            user.level = new_level
        
        db.session.commit()
        return jsonify({
            'message': 'Activities updated successfully',
            'activities_count': len(activities),
            'current_xp': user.current_xp if user else 0,
            'level': user.level if user else 1,
            'level_up': level_up if user else False
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

BASE_XP = 500  # Base XP for completing all daily activities

@tracking_bp.route('/activities/<activity_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_activity(activity_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    try:
        # Find the activity in default activities or custom activities
        activity = None
        default_activities = [
            {'id': '1', 'name': 'Weight Lifting', 'category': 'Mind + Body', 'type': 'exercise'},
            {'id': '2', 'name': 'Reading', 'category': 'Mind + Body', 'type': 'learning'},
            {'id': '3', 'name': 'Family Activity', 'category': 'Purpose + People', 'type': 'social'},
            {'id': '4', 'name': 'Learning New Skill', 'category': 'Growth + Creation', 'type': 'learning'},
            {'id': '5', 'name': 'Boxing', 'category': 'Mind + Body', 'type': 'exercise'},
            {'id': '6', 'name': 'Meditation', 'category': 'Mind + Body', 'type': 'mindfulness'},
            {'id': '7', 'name': 'Online Course', 'category': 'Growth + Creation', 'type': 'learning'},
            {'id': '8', 'name': 'Creative Writing', 'category': 'Growth + Creation', 'type': 'creativity'},
            {'id': '9', 'name': 'Volunteer Work', 'category': 'Purpose + People', 'type': 'social'},
            {'id': '10', 'name': 'Mentoring', 'category': 'Purpose + People', 'type': 'social'}
        ]
        
        # Check default activities first
        activity = next((a for a in default_activities if a['id'] == activity_id), None)
        
        # If not found in defaults, check database
        if not activity:
            db_activity = Activity.query.get(activity_id)
            if db_activity:
                activity = {
                    'id': db_activity.id,
                    'name': db_activity.name,
                    'category': db_activity.category,
                    'type': db_activity.type
                }
        
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404
        
        # Check if activity was already completed today
        today = datetime.now(timezone.utc).date()
        user_activity = UserActivity.query.filter_by(
            user_id=user_id,
            activity_id=activity_id,
            date=today
        ).first()
        
        if user_activity:
            # If already completed, uncomplete it
            db.session.delete(user_activity)
            completed = False
            message = "Activity uncompleted"
            xp_gained = 0
        else:
            # Delete any existing activity for this user and activity_id (regardless of date)
            UserActivity.query.filter_by(
                user_id=user_id,
                activity_id=activity_id
            ).delete()
            
            # Complete the activity
            user_activity = UserActivity(
                id=str(uuid.uuid4()),
                user_id=user_id,
                activity_id=activity_id,
                activity_name=activity['name'],
                category=activity['category'],
                type=activity['type'],
                date=today,
                completed=True,
                is_active=True
            )
            db.session.add(user_activity)
            
            # Calculate XP gain
            base_xp = 500  # Base XP per activity
            multiplier = min(user.streak_days + 1, 4)  # Cap multiplier at 4x
            xp_gained = base_xp * multiplier
            
            # Update user's XP and check for level up
            user.current_xp += xp_gained
            old_level = user.level
            user.level = (user.current_xp // 1000) + 1  # Level up every 1000 XP
            
            completed = True
            message = f"Activity completed! You earned {xp_gained} XP with a {multiplier}x multiplier!"
            
            if user.level > old_level:
                message += f" Level up! You are now level {user.level}!"
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'completed': completed,
            'level': user.level,
            'current_xp': user.current_xp,
            'xp_to_next_level': 1000,  # Fixed XP per level
            'streak_days': user.streak_days,
            'multiplier': min(user.streak_days + 1, 4),
            'xp_gained': xp_gained
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error toggling activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/custom-activities', methods=['GET'])
@jwt_required()
def get_custom_activities():
    user_id = get_jwt_identity()
    
    # Get all custom activities for the user
    custom_activities = Activity.query.filter_by(
        user_id=user_id,
        is_custom=True
    ).all()
    
    return jsonify({
        'activities': [{
            'id': activity.id,
            'name': activity.name,
            'category': activity.category,
            'type': activity.type,
            'is_custom': activity.is_custom
        } for activity in custom_activities]
    })

@tracking_bp.route('/custom-activities', methods=['POST'])
@jwt_required()
def create_custom_activity():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create new custom activity
    new_activity = Activity(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        category=data['category'],
        type=data.get('type', 'custom'),
        is_custom=True
    )
    
    db.session.add(new_activity)
    db.session.commit()
    
    return jsonify({
        'id': new_activity.id,
        'name': new_activity.name,
        'category': new_activity.category,
        'type': new_activity.type,
        'is_custom': new_activity.is_custom
    }), 201

@tracking_bp.route('/custom-activities/<activity_id>', methods=['DELETE'])
@jwt_required()
def delete_custom_activity(activity_id):
    try:
        user_id = get_jwt_identity()
        
        # Find the custom activity
        activity = Activity.query.filter_by(
            id=activity_id,
            is_custom=True
        ).first()
        
        if not activity:
            return jsonify({'error': 'Custom activity not found'}), 404
            
        # Delete the activity
        db.session.delete(activity)
        
        # Also delete any user activity references
        UserActivity.query.filter_by(
            activity_id=activity_id
        ).delete()
        
        db.session.commit()
        
        return jsonify({'message': 'Custom activity deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting custom activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/user-stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Get today's completed activities count
    today = datetime.now(timezone.utc).date()
    completed_today = UserActivity.query.filter_by(
        user_id=user_id,
        date=today
    ).count()
    
    # Get total selected activities
    selected_activities = Activity.query.join(UserActivity).filter(
        UserActivity.user_id == user_id
    ).distinct().count()
    
    return jsonify({
        'level': user.level,
        'current_xp': user.current_xp,
        'xp_to_next_level': user.xp_to_next_level,
        'streak_days': user.streak_days,
        'multiplier': user.multiplier,
        'completed_today': completed_today,
        'total_activities': selected_activities
    }) 
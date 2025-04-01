from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.tracking import Journal, WeightLog, ProgressPhoto
from app.models.activity import Activity, UserActivity
from app.models.user import User
from app.extensions import db
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func, and_, or_
import json
from app.decorators import token_required
import math

tracking_bp = Blueprint('tracking', __name__)

def calculate_xp_for_level(level):
    """Calculate XP needed for a specific level."""
    return int(500 + pow(level, 1.5))

def get_current_level_and_next_xp(total_xp):
    """
    Calculate current level and XP needed for next level based on total XP.
    Returns (current_level, xp_needed_for_next_level)
    """
    level = 1
    while True:
        next_level_xp = calculate_xp_for_level(level + 1)
        if total_xp < next_level_xp:
            return level, next_level_xp
        level += 1

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
@tracking_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    # Redirect to all-activities endpoint to ensure consistency
    return get_all_activities()

@tracking_bp.route('/activities', methods=['POST'])
@jwt_required()
def update_selected_activities():
    user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        selected_activities = data.get('selected_activities', [])
        
        # Validate the data structure
        if not isinstance(selected_activities, list):
            return jsonify({'error': 'Invalid data format'}), 400
        
        # Get all current active selections for the user
        current_selections = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.is_active == True
        ).all()
        
        # Deactivate all current selections
        for selection in current_selections:
            selection.is_active = False
        
        # Create or update new selections
        today = datetime.now(timezone.utc).date()
        for activity_id in selected_activities:
            # Get the activity details
            activity = Activity.query.get(activity_id)
            if not activity:
                continue
                
            # Try to find any existing record for this activity (regardless of date)
            user_activity = UserActivity.query.filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_id == activity_id
            ).first()
            
            if user_activity:
                # Update existing record
                user_activity.is_active = True
                user_activity.date = today  # Update the date to today
                user_activity.completed = False  # Reset completion status
                user_activity.is_completed_today = False  # Reset daily completion
            else:
                # Create new record
                new_selection = UserActivity(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    activity_id=activity_id,
                    activity_name=activity.name,
                    category=activity.category,
                    type=activity.type,
                    date=today,
                    is_active=True,
                    completed=False,
                    is_completed_today=False
                )
                db.session.add(new_selection)
        
        db.session.commit()
        return jsonify({'message': 'Activities updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating activities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tracking_bp.route('/all-activities', methods=['GET'])
@jwt_required()
def get_all_activities():
    user_id = get_jwt_identity()
    
    try:
        print(f"[DEBUG] Fetching activities for user {user_id}")
        
        # Get default activities and user's custom activities
        activities = Activity.query.filter(
            or_(
                and_(Activity.user_id.is_(None), Activity.is_active == True),  # Default activities
                and_(Activity.user_id == user_id, Activity.is_custom == True)   # User's custom activities
            )
        ).all()
        
        print(f"[DEBUG] Found {len(activities)} total activities")
        
        # Get today's date
        today = datetime.now(timezone.utc).date()
        
        # Get user's active selections and completed activities for today
        user_activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            or_(
                UserActivity.is_active == True,  # Get all active selections
                and_(UserActivity.date == today, UserActivity.is_completed_today == True)  # Get today's completed activities
            )
        ).all()
        
        print(f"[DEBUG] Found {len(user_activities)} user activities")
        
        # Create sets for quick lookups
        selected_activity_ids = {ua.activity_id for ua in user_activities if ua.is_active}
        completed_activity_ids = {ua.activity_id for ua in user_activities if ua.is_completed_today}
        
        print(f"[DEBUG] Active activity IDs: {selected_activity_ids}")
        print(f"[DEBUG] Completed activity IDs: {completed_activity_ids}")
        
        # Create a list of all activities with their selection status
        activities_list = []
        categorized_activities = {}
        
        for activity in activities:
            is_active = activity.id in selected_activity_ids
            completed_today = activity.id in completed_activity_ids
            print(f"[DEBUG] Activity {activity.id} ({activity.name}) - is_active: {is_active}, completed_today: {completed_today}")
            
            activity_data = {
                'id': activity.id,
                'name': activity.name,
                'category': activity.category,
                'type': activity.type,
                'is_custom': activity.is_custom,
                'is_active': is_active,
                'completed_today': completed_today
            }
            
            activities_list.append(activity_data)
            
            # Organize by category
            if activity.category not in categorized_activities:
                categorized_activities[activity.category] = []
            categorized_activities[activity.category].append(activity_data)
        
        print(f"[DEBUG] Returning {len(activities_list)} activities")
        return jsonify({
            'activities': activities_list,
            'categorized_activities': categorized_activities
        })
        
    except Exception as e:
        print(f"[ERROR] Error fetching activities: {str(e)}")
        return jsonify({
            'activities': [],
            'categorized_activities': {}
        }), 500

BASE_XP = 500  # Base XP for completing all daily activities

@tracking_bp.route('/activities/<activity_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_activity(activity_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    try:
        print(f"[DEBUG] Toggle activity request for user {user_id}, activity {activity_id}")
        print(f"[DEBUG] Initial user state - Level: {user.level}, XP: {user.current_xp}, Streak: {user.streak_days}")
        
        # Find the activity
        db_activity = Activity.query.get(activity_id)
        if not db_activity:
            return jsonify({'error': 'Activity not found'}), 404
        
        # Get today's and yesterday's dates
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        # Check if this is a completion request or just a selection toggle
        is_completion = False
        if request.args.get('complete', 'false').lower() == 'true':
            is_completion = True
        elif request.is_json and request.get_json():
            is_completion = request.get_json().get('is_completion', False)
            
        print(f"[DEBUG] Request type - is_completion: {is_completion}")
        
        # Initialize response values
        message = ""
        xp_gained = 0
        new_level = user.level
        xp_to_next = calculate_xp_for_level(user.level + 1)
        current_multiplier = 1  # Default multiplier
        
        # First, try to find any existing record for this activity (regardless of date)
        existing_activity = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_id == activity_id
        ).first()
        
        if existing_activity:
            print(f"[DEBUG] Found existing activity record - current state: completed={existing_activity.completed}, is_active={existing_activity.is_active}")
            
            # Update the existing record
            if is_completion:
                # Only complete if not already completed today
                if not existing_activity.is_completed_today:
                    existing_activity.completed = True
                    existing_activity.is_completed_today = True
                    # Don't modify is_active when completing
                    print(f"[DEBUG] Completing activity - preserving is_active={existing_activity.is_active}")
                    
                    # Calculate XP gain using current streak (before any updates)
                    base_xp = 100
                    
                    # Check if user completed any activities yesterday
                    yesterday_completed = UserActivity.query.filter(
                        UserActivity.user_id == user_id,
                        UserActivity.date == yesterday,
                        UserActivity.is_completed_today == True
                    ).count() > 0
                    
                    # Update streak based on yesterday's completion
                    if yesterday_completed:
                        user.streak_days = min(user.streak_days + 1, 4)
                        print(f"[DEBUG] Streak continued - new streak: {user.streak_days}")
                    else:
                        user.streak_days = 1
                        print(f"[DEBUG] Streak reset - new streak: 1")
                    
                    # Calculate multiplier based on current streak
                    current_multiplier = max(1, min(user.streak_days, 4))
                    xp_gained = base_xp * current_multiplier
                    print(f"[DEBUG] XP Calculation - Base XP: {base_xp}, Current Streak: {user.streak_days}, Multiplier: {current_multiplier}")
                    
                    # Update user's XP
                    user.current_xp += xp_gained
                    
                    # Calculate new level based on current XP
                    new_level, xp_to_next = get_current_level_and_next_xp(user.current_xp)
                    user.level = new_level
                    
                    message = f"Activity completed! You earned {xp_gained} XP with a {current_multiplier}x multiplier!"
                    if new_level > user.level:
                        message += f" Level up! You are now level {new_level}!"
                    
                    print(f"[DEBUG] Activity completed - XP gained: {xp_gained}, New streak: {user.streak_days}")
                else:
                    message = "Activity already completed today"
                    print("[DEBUG] Activity was already completed today - no changes made")
                    return jsonify({
                        'message': message,
                        'completed': True,
                        'is_active': existing_activity.is_active,
                        'level': user.level,
                        'current_xp': user.current_xp,
                        'streak_days': user.streak_days,
                        'multiplier': current_multiplier
                    })
            else:
                # Just toggle selection state
                existing_activity.is_active = not existing_activity.is_active
                message = "Activity selection updated"
                print(f"[DEBUG] Toggled selection state - new is_active: {existing_activity.is_active}")
        else:
            # Create new record if none exists
            new_activity = UserActivity(
                id=str(uuid.uuid4()),
                user_id=user_id,
                activity_id=activity_id,
                activity_name=db_activity.name,
                category=db_activity.category,
                type=db_activity.type,
                date=today,
                completed=is_completion,
                is_completed_today=is_completion,
                is_active=True  # Always set is_active to true for new records
            )
            db.session.add(new_activity)
            print(f"[DEBUG] Created new activity record - completed: {is_completion}, is_active: true")
            message = "Activity selection created"
            
            # If this is a completion, handle XP and streak updates
            if is_completion:
                base_xp = 100
                
                # Check if user completed any activities yesterday
                yesterday_completed = UserActivity.query.filter(
                    UserActivity.user_id == user_id,
                    UserActivity.date == yesterday,
                    UserActivity.is_completed_today == True
                ).count() > 0
                
                # Update streak based on yesterday's completion
                if yesterday_completed:
                    user.streak_days = min(user.streak_days + 1, 4)
                    print(f"[DEBUG] Streak continued - new streak: {user.streak_days}")
                else:
                    user.streak_days = 1
                    print(f"[DEBUG] Streak reset - new streak: 1")
                
                # Calculate multiplier based on current streak
                current_multiplier = max(1, min(user.streak_days, 4))
                xp_gained = base_xp * current_multiplier
                user.current_xp += xp_gained
                new_level, xp_to_next = get_current_level_and_next_xp(user.current_xp)
                user.level = new_level
        
        db.session.commit()
        
        print(f"[DEBUG] Final user state - Level: {user.level}, XP: {user.current_xp}, Streak: {user.streak_days}")
        
        # Return appropriate response based on operation type
        if is_completion:
            return jsonify({
                'message': message,
                'completed': True,
                'level': new_level,
                'current_xp': user.current_xp,
                'xp_to_next_level': xp_to_next,
                'streak_days': user.streak_days,
                'multiplier': current_multiplier,
                'xp_gained': xp_gained,
                'is_active': existing_activity.is_active if existing_activity else True
            })
        else:
            return jsonify({
                'message': message,
                'completed': False,
                'is_active': existing_activity.is_active if existing_activity else True,
                'level': user.level,
                'current_xp': user.current_xp,
                'streak_days': user.streak_days
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error in toggle_activity: {str(e)}")
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
    if not data.get('name'):
        return jsonify({'error': 'Activity name is required'}), 400
    if not data.get('category'):
        return jsonify({'error': 'Activity category is required'}), 400
        
    try:
        # Create new custom activity
        new_activity = Activity(
            id=str(uuid.uuid4()),
            user_id=user_id,  # Associate with the current user
            name=data['name'],
            category=data['category'],
            type=data.get('type', 'custom'),
            is_custom=True,
            is_active=True
        )
        
        db.session.add(new_activity)
        db.session.commit()
        
        return jsonify({
            'id': new_activity.id,
            'name': new_activity.name,
            'category': new_activity.category,
            'type': new_activity.type,
            'is_custom': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating custom activity: {str(e)}")
        return jsonify({'error': 'Failed to create custom activity'}), 500

@tracking_bp.route('/custom-activities/<activity_id>', methods=['DELETE'])
@jwt_required()
def delete_custom_activity(activity_id):
    user_id = get_jwt_identity()
    
    try:
        # Find the activity and verify it belongs to the user
        activity = Activity.query.filter_by(
            id=activity_id,
            user_id=user_id,
            is_custom=True
        ).first_or_404()
        
        # Delete any associated user_activity records
        UserActivity.query.filter_by(activity_id=activity_id).delete()
        
        # Delete the activity
        db.session.delete(activity)
        db.session.commit()
        
        return jsonify({'message': 'Custom activity deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting custom activity: {str(e)}")
        return jsonify({'error': 'Failed to delete custom activity'}), 500

@tracking_bp.route('/user-stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        
        # Calculate current level and XP needed for next level
        current_level, xp_to_next = get_current_level_and_next_xp(user.current_xp)
        
        # Get today's and yesterday's dates
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        # Check if user completed any activities yesterday
        yesterday_completed = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.date == yesterday,
            UserActivity.is_completed_today == True
        ).count() > 0
        
        # Get today's completed activities count
        completed_today = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.is_completed_today == True
        ).count()
        
        # Get total selected (bookmarked) activities
        selected_activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.is_active == True
        ).count()
        
        # Calculate current multiplier based on streak
        current_multiplier = max(1, min(user.streak_days, 4))
        
        print(f"[DEBUG] User stats - Level: {current_level}, XP: {user.current_xp}, Streak: {user.streak_days}, Yesterday completed: {yesterday_completed}")
        
        return jsonify({
            'level': current_level,
            'current_xp': user.current_xp,
            'xp_to_next_level': xp_to_next,
            'streak_days': user.streak_days,
            'multiplier': current_multiplier,
            'completed_today': completed_today,
            'total_activities': selected_activities
        })
    except Exception as e:
        print(f"Error in get_user_stats: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch user stats',
            'level': 1,
            'current_xp': 0,
            'xp_to_next_level': 300,  # Starting XP requirement
            'streak_days': 0,
            'multiplier': 1,
            'completed_today': 0,
            'total_activities': 0
        }), 500 
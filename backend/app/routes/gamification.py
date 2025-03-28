from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import DailyCheckIn, Achievement, WeeklyMission, UserActivityLog
from app.extensions import db
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func
import json

gamification_bp = Blueprint('gamification', __name__)

def get_pagination_params():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return page, per_page

# Daily Check-in Routes
@gamification_bp.route('/check-ins', methods=['GET'])
@jwt_required()
def get_check_ins():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = DailyCheckIn.query.filter_by(user_id=user_id)
    
    # Apply date filters
    start_date = request.args.get('start_date')
    if start_date:
        query = query.filter(DailyCheckIn.date >= datetime.fromisoformat(start_date).date())
    
    end_date = request.args.get('end_date')
    if end_date:
        query = query.filter(DailyCheckIn.date <= datetime.fromisoformat(end_date).date())
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'date')
    if sort_by in ['date', 'completed']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(DailyCheckIn, sort_by)))
        else:
            query = query.order_by(getattr(DailyCheckIn, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    check_ins = pagination.items
    
    return jsonify({
        'items': [{
            'id': c.id,
            'date': c.date.isoformat(),
            'completed': c.completed
        } for c in check_ins],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@gamification_bp.route('/check-ins', methods=['POST'])
@jwt_required()
def create_check_in():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user already checked in today
    today = datetime.now(timezone.utc).date()
    existing_check_in = DailyCheckIn.query.filter_by(
        user_id=user_id,
        date=today
    ).first()
    
    if existing_check_in:
        return jsonify({'error': 'Already checked in today'}), 400
    
    # Create new check-in
    new_check_in = DailyCheckIn(
        id=str(uuid.uuid4()),
        user_id=user_id,
        date=today,
        completed=data.get('completed', True)
    )
    
    db.session.add(new_check_in)
    db.session.commit()
    
    return jsonify({
        'id': new_check_in.id,
        'date': new_check_in.date.isoformat(),
        'completed': new_check_in.completed
    }), 201

@gamification_bp.route('/check-ins/<check_in_id>', methods=['PUT'])
@jwt_required()
def update_check_in(check_in_id):
    user_id = get_jwt_identity()
    check_in = DailyCheckIn.query.filter_by(id=check_in_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'completed' in data:
        check_in.completed = data['completed']
    
    db.session.commit()
    
    return jsonify({
        'id': check_in.id,
        'date': check_in.date.isoformat(),
        'completed': check_in.completed
    })

# Achievement Routes
@gamification_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = Achievement.query
    
    # Apply filters
    min_xp = request.args.get('min_xp', type=float)
    if min_xp is not None:
        query = query.filter(Achievement.xp_reward >= min_xp)
    
    max_xp = request.args.get('max_xp', type=float)
    if max_xp is not None:
        query = query.filter(Achievement.xp_reward <= max_xp)
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'name')
    if sort_by in ['name', 'xp_reward']:
        direction = request.args.get('direction', 'asc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(Achievement, sort_by)))
        else:
            query = query.order_by(getattr(Achievement, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    achievements = pagination.items
    
    return jsonify({
        'items': [{
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'xp_reward': a.xp_reward,
            'condition': json.loads(a.condition) if a.condition else None
        } for a in achievements],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@gamification_bp.route('/achievements', methods=['POST'])
@jwt_required()
def create_achievement():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'xp_reward']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate xp_reward is positive
    if not isinstance(data['xp_reward'], (int, float)) or data['xp_reward'] <= 0:
        return jsonify({'error': 'XP reward must be a positive number'}), 400
    
    # Create new achievement
    new_achievement = Achievement(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description', ''),
        xp_reward=float(data['xp_reward']),
        condition=json.dumps(data.get('condition')) if data.get('condition') else None
    )
    
    db.session.add(new_achievement)
    db.session.commit()
    
    return jsonify({
        'id': new_achievement.id,
        'name': new_achievement.name,
        'description': new_achievement.description,
        'xp_reward': new_achievement.xp_reward,
        'condition': json.loads(new_achievement.condition) if new_achievement.condition else None
    }), 201

@gamification_bp.route('/achievements/<achievement_id>', methods=['PUT'])
@jwt_required()
def update_achievement(achievement_id):
    achievement = Achievement.query.get_or_404(achievement_id)
    data = request.get_json()
    
    if 'name' in data:
        achievement.name = data['name']
    if 'description' in data:
        achievement.description = data['description']
    if 'xp_reward' in data:
        if not isinstance(data['xp_reward'], (int, float)) or data['xp_reward'] <= 0:
            return jsonify({'error': 'XP reward must be a positive number'}), 400
        achievement.xp_reward = float(data['xp_reward'])
    if 'condition' in data:
        achievement.condition = json.dumps(data['condition']) if data['condition'] else None
    
    db.session.commit()
    
    return jsonify({
        'id': achievement.id,
        'name': achievement.name,
        'description': achievement.description,
        'xp_reward': achievement.xp_reward,
        'condition': json.loads(achievement.condition) if achievement.condition else None
    })

@gamification_bp.route('/achievements/<achievement_id>', methods=['DELETE'])
@jwt_required()
def delete_achievement(achievement_id):
    achievement = Achievement.query.get_or_404(achievement_id)
    db.session.delete(achievement)
    db.session.commit()
    return jsonify({'message': 'Achievement deleted successfully'})

# Weekly Mission Routes
@gamification_bp.route('/weekly-missions', methods=['GET'])
@jwt_required()
def get_weekly_missions():
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = WeeklyMission.query
    
    # Apply filters
    min_xp = request.args.get('min_xp', type=float)
    if min_xp is not None:
        query = query.filter(WeeklyMission.xp_reward >= min_xp)
    
    max_xp = request.args.get('max_xp', type=float)
    if max_xp is not None:
        query = query.filter(WeeklyMission.xp_reward <= max_xp)
    
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    if active_only:
        today = datetime.now(timezone.utc).date()
        query = query.filter(
            WeeklyMission.start_date <= today,
            WeeklyMission.end_date >= today
        )
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'start_date')
    if sort_by in ['name', 'xp_reward', 'start_date', 'end_date']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(WeeklyMission, sort_by)))
        else:
            query = query.order_by(getattr(WeeklyMission, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    missions = pagination.items
    
    return jsonify({
        'items': [{
            'id': m.id,
            'name': m.name,
            'description': m.description,
            'xp_reward': m.xp_reward,
            'start_date': m.start_date.isoformat(),
            'end_date': m.end_date.isoformat()
        } for m in missions],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@gamification_bp.route('/weekly-missions', methods=['POST'])
@jwt_required()
def create_weekly_mission():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'xp_reward', 'start_date', 'end_date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate xp_reward is positive
    if not isinstance(data['xp_reward'], (int, float)) or data['xp_reward'] <= 0:
        return jsonify({'error': 'XP reward must be a positive number'}), 400
    
    # Validate dates
    start_date = datetime.fromisoformat(data['start_date']).date()
    end_date = datetime.fromisoformat(data['end_date']).date()
    
    if end_date < start_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    # Create new weekly mission
    new_mission = WeeklyMission(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description', ''),
        xp_reward=float(data['xp_reward']),
        start_date=start_date,
        end_date=end_date
    )
    
    db.session.add(new_mission)
    db.session.commit()
    
    return jsonify({
        'id': new_mission.id,
        'name': new_mission.name,
        'description': new_mission.description,
        'xp_reward': new_mission.xp_reward,
        'start_date': new_mission.start_date.isoformat(),
        'end_date': new_mission.end_date.isoformat()
    }), 201

@gamification_bp.route('/weekly-missions/<mission_id>', methods=['PUT'])
@jwt_required()
def update_weekly_mission(mission_id):
    mission = WeeklyMission.query.get_or_404(mission_id)
    data = request.get_json()
    
    if 'name' in data:
        mission.name = data['name']
    if 'description' in data:
        mission.description = data['description']
    if 'xp_reward' in data:
        if not isinstance(data['xp_reward'], (int, float)) or data['xp_reward'] <= 0:
            return jsonify({'error': 'XP reward must be a positive number'}), 400
        mission.xp_reward = float(data['xp_reward'])
    if 'start_date' in data:
        mission.start_date = datetime.fromisoformat(data['start_date']).date()
    if 'end_date' in data:
        mission.end_date = datetime.fromisoformat(data['end_date']).date()
        
        # Validate dates
        if mission.end_date < mission.start_date:
            return jsonify({'error': 'End date must be after start date'}), 400
    
    db.session.commit()
    
    return jsonify({
        'id': mission.id,
        'name': mission.name,
        'description': mission.description,
        'xp_reward': mission.xp_reward,
        'start_date': mission.start_date.isoformat(),
        'end_date': mission.end_date.isoformat()
    })

@gamification_bp.route('/weekly-missions/<mission_id>', methods=['DELETE'])
@jwt_required()
def delete_weekly_mission(mission_id):
    mission = WeeklyMission.query.get_or_404(mission_id)
    db.session.delete(mission)
    db.session.commit()
    return jsonify({'message': 'Weekly mission deleted successfully'})

# Analytics Routes
@gamification_bp.route('/analytics/check-in-streak', methods=['GET'])
@jwt_required()
def get_check_in_streak():
    user_id = get_jwt_identity()
    
    # Get all check-ins ordered by date
    check_ins = DailyCheckIn.query.filter_by(
        user_id=user_id,
        completed=True
    ).order_by(DailyCheckIn.date.desc()).all()
    
    if not check_ins:
        return jsonify({
            'current_streak': 0,
            'longest_streak': 0,
            'total_check_ins': 0
        })
    
    # Calculate current streak
    current_streak = 1
    today = datetime.now(timezone.utc).date()
    last_check_in = check_ins[0].date
    
    if last_check_in != today:
        current_streak = 0
    else:
        for i in range(1, len(check_ins)):
            if (last_check_in - check_ins[i].date).days == 1:
                current_streak += 1
                last_check_in = check_ins[i].date
            else:
                break
    
    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1
    for i in range(1, len(check_ins)):
        if (check_ins[i-1].date - check_ins[i].date).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    return jsonify({
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_check_ins': len(check_ins)
    })

def evaluate_achievement_condition(condition, user_id):
    """Evaluate an achievement condition based on user's activity."""
    if not condition:
        return 0, False
    
    condition_type = condition.get('type')
    target_value = condition.get('target_value', 0)
    time_period = condition.get('time_period', 'all')  # all, week, month, year
    
    # Calculate date range based on time period
    today = datetime.now(timezone.utc).date()
    if time_period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif time_period == 'month':
        start_date = today.replace(day=1)
    elif time_period == 'year':
        start_date = today.replace(month=1, day=1)
    else:
        start_date = None
    
    # Get user's activities based on condition type
    if condition_type == 'check_in_streak':
        check_ins = DailyCheckIn.query.filter(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.completed == True
        ).order_by(DailyCheckIn.date.desc()).all()
        
        if not check_ins:
            return 0, False
        
        current_streak = 1
        last_check_in = check_ins[0].date
        
        for i in range(1, len(check_ins)):
            if (last_check_in - check_ins[i].date).days == 1:
                current_streak += 1
                last_check_in = check_ins[i].date
            else:
                break
        
        progress = min(current_streak / target_value, 1.0)
        completed = current_streak >= target_value
        return progress, completed
    
    elif condition_type == 'total_xp':
        query = UserActivityLog.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(UserActivityLog.date >= start_date)
        
        total_xp = db.session.query(func.sum(UserActivityLog.xp_earned)).scalar() or 0
        progress = min(total_xp / target_value, 1.0)
        completed = total_xp >= target_value
        return progress, completed
    
    elif condition_type == 'activity_count':
        query = UserActivityLog.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(UserActivityLog.date >= start_date)
        
        count = query.count()
        progress = min(count / target_value, 1.0)
        completed = count >= target_value
        return progress, completed
    
    elif condition_type == 'category_completion':
        category = condition.get('category')
        if not category:
            return 0, False
        
        query = UserActivityLog.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(UserActivityLog.date >= start_date)
        
        count = query.filter(UserActivityLog.activity.has(category=category)).count()
        progress = min(count / target_value, 1.0)
        completed = count >= target_value
        return progress, completed
    
    return 0, False

@gamification_bp.route('/analytics/achievement-progress', methods=['GET'])
@jwt_required()
def get_achievement_progress():
    user_id = get_jwt_identity()
    
    # Get all achievements
    achievements = Achievement.query.all()
    
    # Calculate progress for each achievement
    achievement_progress = []
    for achievement in achievements:
        condition = json.loads(achievement.condition) if achievement.condition else {}
        progress, completed = evaluate_achievement_condition(condition, user_id)
        
        achievement_progress.append({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'xp_reward': achievement.xp_reward,
            'progress': progress,
            'completed': completed
        })
    
    return jsonify({
        'achievements': achievement_progress,
        'total_achievements': len(achievements),
        'completed_achievements': sum(1 for a in achievement_progress if a['completed'])
    })

@gamification_bp.route('/analytics/weekly-mission-progress', methods=['GET'])
@jwt_required()
def get_weekly_mission_progress():
    user_id = get_jwt_identity()
    
    # Get current week's missions
    today = datetime.now(timezone.utc).date()
    current_missions = WeeklyMission.query.filter(
        WeeklyMission.start_date <= today,
        WeeklyMission.end_date >= today
    ).all()
    
    # Get user's check-ins for the current week
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    weekly_check_ins = DailyCheckIn.query.filter(
        DailyCheckIn.user_id == user_id,
        DailyCheckIn.date >= week_start,
        DailyCheckIn.date <= week_end,
        DailyCheckIn.completed == True
    ).all()
    
    # Calculate progress for each mission
    mission_progress = []
    for mission in current_missions:
        # Example progress calculation (you'll need to implement your own logic)
        progress = {
            'id': mission.id,
            'name': mission.name,
            'description': mission.description,
            'xp_reward': mission.xp_reward,
            'progress': 0,  # This should be calculated based on your mission completion logic
            'completed': False
        }
        
        mission_progress.append(progress)
    
    return jsonify({
        'current_missions': mission_progress,
        'total_missions': len(current_missions),
        'completed_missions': sum(1 for m in mission_progress if m['completed'])
    })

# New Analytics Endpoints
@gamification_bp.route('/analytics/xp-summary', methods=['GET'])
@jwt_required()
def get_xp_summary():
    user_id = get_jwt_identity()
    
    # Get total XP earned
    total_xp = db.session.query(func.sum(UserActivityLog.xp_earned)).filter_by(user_id=user_id).scalar() or 0
    
    # Get XP earned this week
    week_start = datetime.now(timezone.utc).date() - timedelta(days=datetime.now(timezone.utc).weekday())
    weekly_xp = db.session.query(func.sum(UserActivityLog.xp_earned)).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.date >= week_start
    ).scalar() or 0
    
    # Get XP earned this month
    month_start = datetime.now(timezone.utc).date().replace(day=1)
    monthly_xp = db.session.query(func.sum(UserActivityLog.xp_earned)).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.date >= month_start
    ).scalar() or 0
    
    # Calculate level (assuming 1000 XP per level)
    current_level = (total_xp // 1000) + 1
    xp_for_next_level = 1000 - (total_xp % 1000)
    
    return jsonify({
        'total_xp': total_xp,
        'weekly_xp': weekly_xp,
        'monthly_xp': monthly_xp,
        'current_level': current_level,
        'xp_for_next_level': xp_for_next_level,
        'level_progress': (total_xp % 1000) / 1000
    })

@gamification_bp.route('/analytics/activity-stats', methods=['GET'])
@jwt_required()
def get_activity_stats():
    user_id = get_jwt_identity()
    
    # Get time period from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    # Get activity counts by category
    category_stats = db.session.query(
        UserActivityLog.activity.has(category=category).label('category'),
        func.count().label('count'),
        func.sum(UserActivityLog.xp_earned).label('total_xp')
    ).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.date >= start_date
    ).group_by('category').all()
    
    # Get daily activity counts
    daily_stats = db.session.query(
        UserActivityLog.date,
        func.count().label('count'),
        func.sum(UserActivityLog.xp_earned).label('total_xp')
    ).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.date >= start_date
    ).group_by(UserActivityLog.date).all()
    
    return jsonify({
        'category_stats': [{
            'category': s.category,
            'count': s.count,
            'total_xp': float(s.total_xp) if s.total_xp else 0
        } for s in category_stats],
        'daily_stats': [{
            'date': s.date.isoformat(),
            'count': s.count,
            'total_xp': float(s.total_xp) if s.total_xp else 0
        } for s in daily_stats]
    }) 
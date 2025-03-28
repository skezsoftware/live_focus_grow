from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Asset, MonthlyExpense, Income, FinancialGoal
from app.extensions import db
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc

finance_bp = Blueprint('finance', __name__)

def get_pagination_params():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return page, per_page

# Asset Routes
@finance_bp.route('/assets', methods=['GET'])
@jwt_required()
def get_assets():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = Asset.query.filter_by(user_id=user_id)
    
    # Apply filters
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    min_value = request.args.get('min_value', type=float)
    if min_value is not None:
        query = query.filter(Asset.value >= min_value)
    
    max_value = request.args.get('max_value', type=float)
    if max_value is not None:
        query = query.filter(Asset.value <= max_value)
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'name')
    if sort_by in ['name', 'value', 'purchase_date']:
        direction = request.args.get('direction', 'asc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(Asset, sort_by)))
        else:
            query = query.order_by(getattr(Asset, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    assets = pagination.items
    
    return jsonify({
        'items': [{
            'id': a.id,
            'name': a.name,
            'category': a.category,
            'value': a.value,
            'purchase_date': a.purchase_date.isoformat() if a.purchase_date else None,
            'notes': a.notes
        } for a in assets],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@finance_bp.route('/assets', methods=['POST'])
@jwt_required()
def create_asset():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'value']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate value is positive
    if not isinstance(data['value'], (int, float)) or data['value'] <= 0:
        return jsonify({'error': 'Value must be a positive number'}), 400
    
    # Create new asset
    new_asset = Asset(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        category=data.get('category'),
        value=float(data['value']),
        purchase_date=datetime.fromisoformat(data['purchase_date']) if data.get('purchase_date') else None,
        notes=data.get('notes', '')
    )
    
    db.session.add(new_asset)
    db.session.commit()
    
    return jsonify({
        'id': new_asset.id,
        'name': new_asset.name,
        'category': new_asset.category,
        'value': new_asset.value,
        'purchase_date': new_asset.purchase_date.isoformat() if new_asset.purchase_date else None,
        'notes': new_asset.notes
    }), 201

@finance_bp.route('/assets/<asset_id>', methods=['PUT'])
@jwt_required()
def update_asset(asset_id):
    user_id = get_jwt_identity()
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'name' in data:
        asset.name = data['name']
    if 'category' in data:
        asset.category = data['category']
    if 'value' in data:
        if not isinstance(data['value'], (int, float)) or data['value'] <= 0:
            return jsonify({'error': 'Value must be a positive number'}), 400
        asset.value = float(data['value'])
    if 'purchase_date' in data:
        asset.purchase_date = datetime.fromisoformat(data['purchase_date']) if data['purchase_date'] else None
    if 'notes' in data:
        asset.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'id': asset.id,
        'name': asset.name,
        'category': asset.category,
        'value': asset.value,
        'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
        'notes': asset.notes
    })

@finance_bp.route('/assets/<asset_id>', methods=['DELETE'])
@jwt_required()
def delete_asset(asset_id):
    user_id = get_jwt_identity()
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first_or_404()
    db.session.delete(asset)
    db.session.commit()
    return jsonify({'message': 'Asset deleted successfully'})

# Monthly Expense Routes
@finance_bp.route('/monthly-expenses', methods=['GET'])
@jwt_required()
def get_monthly_expenses():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = MonthlyExpense.query.filter_by(user_id=user_id)
    
    # Apply filters
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    min_amount = request.args.get('min_amount', type=float)
    if min_amount is not None:
        query = query.filter(MonthlyExpense.amount >= min_amount)
    
    max_amount = request.args.get('max_amount', type=float)
    if max_amount is not None:
        query = query.filter(MonthlyExpense.amount <= max_amount)
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'name')
    if sort_by in ['name', 'amount', 'due_date']:
        direction = request.args.get('direction', 'asc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(MonthlyExpense, sort_by)))
        else:
            query = query.order_by(getattr(MonthlyExpense, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    expenses = pagination.items
    
    return jsonify({
        'items': [{
            'id': e.id,
            'name': e.name,
            'category': e.category,
            'amount': e.amount,
            'due_date': e.due_date,
            'is_recurring': e.is_recurring
        } for e in expenses],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@finance_bp.route('/monthly-expenses', methods=['POST'])
@jwt_required()
def create_monthly_expense():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'amount', 'due_date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate amount is positive
    if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({'error': 'Amount must be a positive number'}), 400
    
    # Validate due_date is between 1 and 31
    if not isinstance(data['due_date'], int) or data['due_date'] < 1 or data['due_date'] > 31:
        return jsonify({'error': 'Due date must be between 1 and 31'}), 400
    
    # Create new monthly expense
    new_expense = MonthlyExpense(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        category=data.get('category'),
        amount=float(data['amount']),
        due_date=data['due_date'],
        is_recurring=data.get('is_recurring', True)
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    return jsonify({
        'id': new_expense.id,
        'name': new_expense.name,
        'category': new_expense.category,
        'amount': new_expense.amount,
        'due_date': new_expense.due_date,
        'is_recurring': new_expense.is_recurring
    }), 201

@finance_bp.route('/monthly-expenses/<expense_id>', methods=['PUT'])
@jwt_required()
def update_monthly_expense(expense_id):
    user_id = get_jwt_identity()
    expense = MonthlyExpense.query.filter_by(id=expense_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'name' in data:
        expense.name = data['name']
    if 'category' in data:
        expense.category = data['category']
    if 'amount' in data:
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            return jsonify({'error': 'Amount must be a positive number'}), 400
        expense.amount = float(data['amount'])
    if 'due_date' in data:
        if not isinstance(data['due_date'], int) or data['due_date'] < 1 or data['due_date'] > 31:
            return jsonify({'error': 'Due date must be between 1 and 31'}), 400
        expense.due_date = data['due_date']
    if 'is_recurring' in data:
        expense.is_recurring = data['is_recurring']
    
    db.session.commit()
    
    return jsonify({
        'id': expense.id,
        'name': expense.name,
        'category': expense.category,
        'amount': expense.amount,
        'due_date': expense.due_date,
        'is_recurring': expense.is_recurring
    })

@finance_bp.route('/monthly-expenses/<expense_id>', methods=['DELETE'])
@jwt_required()
def delete_monthly_expense(expense_id):
    user_id = get_jwt_identity()
    expense = MonthlyExpense.query.filter_by(id=expense_id, user_id=user_id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Monthly expense deleted successfully'})

# Income Routes
@finance_bp.route('/income', methods=['GET'])
@jwt_required()
def get_income():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params()
    
    # Build query with filters
    query = Income.query.filter_by(user_id=user_id)
    
    # Apply filters
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    min_amount = request.args.get('min_amount', type=float)
    if min_amount is not None:
        query = query.filter(Income.amount >= min_amount)
    
    max_amount = request.args.get('max_amount', type=float)
    if max_amount is not None:
        query = query.filter(Income.amount <= max_amount)
    
    start_date = request.args.get('start_date')
    if start_date:
        query = query.filter(Income.date >= datetime.fromisoformat(start_date))
    
    end_date = request.args.get('end_date')
    if end_date:
        query = query.filter(Income.date <= datetime.fromisoformat(end_date))
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'date')
    if sort_by in ['name', 'amount', 'date']:
        direction = request.args.get('direction', 'desc')
        if direction == 'desc':
            query = query.order_by(desc(getattr(Income, sort_by)))
        else:
            query = query.order_by(getattr(Income, sort_by))
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page)
    income = pagination.items
    
    return jsonify({
        'items': [{
            'id': i.id,
            'name': i.name,
            'category': i.category,
            'amount': i.amount,
            'date': i.date.isoformat(),
            'is_recurring': i.is_recurring,
            'frequency': i.frequency,
            'notes': i.notes
        } for i in income],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@finance_bp.route('/income', methods=['POST'])
@jwt_required()
def create_income():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'amount', 'date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate amount is positive
    if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({'error': 'Amount must be a positive number'}), 400
    
    # Validate frequency if is_recurring is True
    if data.get('is_recurring', False):
        if 'frequency' not in data or data['frequency'] not in ['daily', 'weekly', 'monthly']:
            return jsonify({'error': 'Frequency must be one of: daily, weekly, monthly'}), 400
    
    # Create new income
    new_income = Income(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        category=data.get('category'),
        amount=float(data['amount']),
        date=datetime.fromisoformat(data['date']),
        is_recurring=data.get('is_recurring', False),
        frequency=data.get('frequency'),
        notes=data.get('notes', '')
    )
    
    db.session.add(new_income)
    db.session.commit()
    
    return jsonify({
        'id': new_income.id,
        'name': new_income.name,
        'category': new_income.category,
        'amount': new_income.amount,
        'date': new_income.date.isoformat(),
        'is_recurring': new_income.is_recurring,
        'frequency': new_income.frequency,
        'notes': new_income.notes
    }), 201

@finance_bp.route('/income/<income_id>', methods=['PUT'])
@jwt_required()
def update_income(income_id):
    user_id = get_jwt_identity()
    income = Income.query.filter_by(id=income_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'name' in data:
        income.name = data['name']
    if 'category' in data:
        income.category = data['category']
    if 'amount' in data:
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            return jsonify({'error': 'Amount must be a positive number'}), 400
        income.amount = float(data['amount'])
    if 'date' in data:
        income.date = datetime.fromisoformat(data['date'])
    if 'is_recurring' in data:
        income.is_recurring = data['is_recurring']
    if 'frequency' in data:
        if data['frequency'] not in ['daily', 'weekly', 'monthly']:
            return jsonify({'error': 'Frequency must be one of: daily, weekly, monthly'}), 400
        income.frequency = data['frequency']
    if 'notes' in data:
        income.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'id': income.id,
        'name': income.name,
        'category': income.category,
        'amount': income.amount,
        'date': income.date.isoformat(),
        'is_recurring': income.is_recurring,
        'frequency': income.frequency,
        'notes': income.notes
    })

@finance_bp.route('/income/<income_id>', methods=['DELETE'])
@jwt_required()
def delete_income(income_id):
    user_id = get_jwt_identity()
    income = Income.query.filter_by(id=income_id, user_id=user_id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    return jsonify({'message': 'Income entry deleted successfully'})

# Financial Goal Routes
@finance_bp.route('/financial-goals', methods=['GET'])
@jwt_required()
def get_financial_goals():
    user_id = get_jwt_identity()
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'target_amount': g.target_amount,
        'current_amount': g.current_amount,
        'deadline': g.deadline.isoformat() if g.deadline else None,
        'category': g.category,
        'status': g.status
    } for g in goals])

@finance_bp.route('/financial-goals', methods=['POST'])
@jwt_required()
def create_financial_goal():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'target_amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate target_amount is positive
    if not isinstance(data['target_amount'], (int, float)) or data['target_amount'] <= 0:
        return jsonify({'error': 'Target amount must be a positive number'}), 400
    
    # Create new financial goal
    new_goal = FinancialGoal(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        target_amount=float(data['target_amount']),
        current_amount=data.get('current_amount', 0),
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
        category=data.get('category'),
        status=data.get('status', 'In Progress')
    )
    
    db.session.add(new_goal)
    db.session.commit()
    
    return jsonify({
        'id': new_goal.id,
        'name': new_goal.name,
        'target_amount': new_goal.target_amount,
        'current_amount': new_goal.current_amount,
        'deadline': new_goal.deadline.isoformat() if new_goal.deadline else None,
        'category': new_goal.category,
        'status': new_goal.status
    }), 201

@finance_bp.route('/financial-goals/<goal_id>/progress', methods=['PUT'])
@jwt_required()
def update_goal_progress(goal_id):
    user_id = get_jwt_identity()
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'current_amount' not in data:
        return jsonify({'error': 'Current amount is required'}), 400
    
    if not isinstance(data['current_amount'], (int, float)) or data['current_amount'] < 0:
        return jsonify({'error': 'Current amount must be a non-negative number'}), 400
    
    goal.current_amount = float(data['current_amount'])
    
    # Update status based on progress
    if goal.current_amount >= goal.target_amount:
        goal.status = 'Completed'
    elif goal.deadline and datetime.now(timezone.utc) > goal.deadline:
        goal.status = 'Failed'
    
    db.session.commit()
    
    return jsonify({
        'id': goal.id,
        'name': goal.name,
        'target_amount': goal.target_amount,
        'current_amount': goal.current_amount,
        'deadline': goal.deadline.isoformat() if goal.deadline else None,
        'category': goal.category,
        'status': goal.status
    })

# Analytics Routes
@finance_bp.route('/analytics/summary', methods=['GET'])
@jwt_required()
def get_financial_summary():
    user_id = get_jwt_identity()
    
    # Calculate total assets
    total_assets = db.session.query(db.func.sum(Asset.value)).filter_by(user_id=user_id).scalar() or 0
    
    # Calculate total monthly expenses
    total_monthly_expenses = db.session.query(db.func.sum(MonthlyExpense.amount)).filter_by(user_id=user_id).scalar() or 0
    
    # Calculate total income for current month
    current_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_monthly_income = db.session.query(db.func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.date >= current_month_start
    ).scalar() or 0
    
    # Calculate recurring income
    recurring_income = db.session.query(db.func.sum(Income.amount)).filter_by(
        user_id=user_id,
        is_recurring=True
    ).scalar() or 0
    
    # Calculate financial goals progress
    active_goals = FinancialGoal.query.filter_by(
        user_id=user_id,
        status='In Progress'
    ).all()
    
    goals_summary = [{
        'name': goal.name,
        'target_amount': goal.target_amount,
        'current_amount': goal.current_amount,
        'progress_percentage': (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0,
        'deadline': goal.deadline.isoformat() if goal.deadline else None
    } for goal in active_goals]
    
    return jsonify({
        'total_assets': total_assets,
        'total_monthly_expenses': total_monthly_expenses,
        'total_monthly_income': total_monthly_income,
        'recurring_income': recurring_income,
        'monthly_savings': total_monthly_income - total_monthly_expenses,
        'active_goals': goals_summary
    })

@finance_bp.route('/analytics/income-expenses', methods=['GET'])
@jwt_required()
def get_income_expenses_trend():
    user_id = get_jwt_identity()
    
    # Get date range from query parameters
    months = request.args.get('months', 12, type=int)
    end_date = datetime.now(timezone.utc)
    start_date = end_date.replace(day=1) - timedelta(days=30 * months)
    
    # Get monthly income
    monthly_income = db.session.query(
        db.func.date_trunc('month', Income.date).label('month'),
        db.func.sum(Income.amount).label('total')
    ).filter(
        Income.user_id == user_id,
        Income.date >= start_date
    ).group_by('month').all()
    
    # Get monthly expenses
    monthly_expenses = db.session.query(
        db.func.date_trunc('month', MonthlyExpense.created_at).label('month'),
        db.func.sum(MonthlyExpense.amount).label('total')
    ).filter(
        MonthlyExpense.user_id == user_id,
        MonthlyExpense.created_at >= start_date
    ).group_by('month').all()
    
    # Format response
    income_data = [{'month': m.month.isoformat(), 'amount': float(m.total)} for m in monthly_income]
    expense_data = [{'month': m.month.isoformat(), 'amount': float(m.total)} for m in monthly_expenses]
    
    return jsonify({
        'income': income_data,
        'expenses': expense_data
    }) 
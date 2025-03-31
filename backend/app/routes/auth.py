from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    # Debug logging
    print("Registration endpoint hit")
    print("Request method:", request.method)
    print("Request headers:", dict(request.headers))
    print("Content-Type:", request.headers.get('Content-Type'))
    print("Raw request data:", request.get_data(as_text=True))

    try:
        if request.method == 'OPTIONS':
            response = current_app.make_default_options_response()
            return response

        # Check Content-Type header
        if not request.is_json:
            print("Error: Request Content-Type is not application/json")
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        # Get JSON data
        try:
            data = request.get_json()
            print("Parsed JSON data:", data)
        except Exception as e:
            print("JSON parsing error:", str(e))
            return jsonify({'error': 'Invalid JSON format'}), 400

        if not data:
            print("Error: No data provided in request")
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            print(f"Error: Missing fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate email format
        if '@' not in data['email']:
            print("Error: Invalid email format")
            return jsonify({'error': 'Invalid email format'}), 400

        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            print(f"Error: Email {data['email']} already registered")
            return jsonify({'error': 'Email already registered'}), 409
            
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            print(f"Error: Username {data['username']} already taken")
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        try:
            user = User(
                id=str(uuid.uuid4()),
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password'])
            )
            
            db.session.add(user)
            db.session.commit()
            print(f"User created successfully: {user.username}")
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            response_data = {
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'access_token': access_token
            }
            
            return jsonify(response_data), 201
            
        except Exception as e:
            print("Database error:", str(e))
            db.session.rollback()
            return jsonify({'error': 'Database error occurred'}), 500
        
    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({'error': 'Registration failed: ' + str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        if not all(field in data for field in ['email', 'password']):
            return jsonify({'error': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'access_token': access_token
        })
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        return jsonify({
            'message': f'Protected route accessed by {user.username}',
            'user_id': current_user_id
        })
    except Exception as e:
        print(f"Protected route error: {str(e)}")
        return jsonify({'error': 'Access denied'}), 401
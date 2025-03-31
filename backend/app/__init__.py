from flask import Flask, jsonify, request
from config import Config, TestingConfig
from flask_cors import CORS
from app.extensions import db, migrate, jwt
from flask_jwt_extended import JWTManager
from datetime import timedelta

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Select configuration
    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Set port to avoid conflict with AirPlay
    app.config['PORT'] = 5001

    # Enable debug mode and full error reporting
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize CORS with proper configuration
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://localhost:5001"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"],
            "max_age": 120  # Cache preflight requests for 2 minutes
        }
    })
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in ['http://localhost:3000', 'http://localhost:5001']:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
        return response

    # Initialize JWT
    jwt = JWTManager(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.tracking import tracking_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(tracking_bp, url_prefix='/api/tracking')

    @app.route('/')
    def test_route():
        return jsonify({'message': 'Hello from Live Focus Grow API'})

    # Add debug route to list all registered routes
    @app.route('/debug/routes')
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        return jsonify(routes)

    return app
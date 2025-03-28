from flask import Flask, jsonify
from config import Config, TestingConfig
from flask_cors import CORS
from app.extensions import db, migrate, jwt

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Select configuration
    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    jwt.init_app(app)

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
from flask import Flask
from config import Config
from app.extensions import db, migrate, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Import models after db is defined
    from app.models import User, Activity, UserActivityLog

    @app.route('/test')
    def test_route():
        return {'message': 'Hello from Live Focus Grow API'}
    
    return app
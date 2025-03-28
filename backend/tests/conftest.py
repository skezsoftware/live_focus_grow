import pytest
from app import create_app
from app.extensions import db
from app.models import User
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    # Create a new database for testing
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            id=str(uuid.uuid4()),
            email='test@example.com',
            username='testuser',
            password_hash=generate_password_hash('testpassword')
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_tokens(client, test_user):
    """Get authentication tokens for the test user."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    return response.get_json() 
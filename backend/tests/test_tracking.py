import pytest
from datetime import datetime, timezone, timedelta
from app.models import Journal, WeightLog, ProgressPhoto, User
from app.extensions import db

def test_get_journals(client, auth_tokens):
    """Test getting journals with pagination and filters"""
    # Create test user and journals
    user = User.query.first()
    journals = [
        Journal(
            id=f'journal-{i}',
            user_id=user.id,
            title=f'Test Journal {i}',
            content=f'Test Content {i}',
            mood='happy' if i % 2 == 0 else 'sad',
            created_at=datetime.now(timezone.utc) - timedelta(days=i)
        ) for i in range(15)
    ]
    db.session.add_all(journals)
    db.session.commit()
    
    # Test without filters
    response = client.get('/api/tracking/journals', headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 10  # Default page size
    assert data['total'] == 15
    assert data['pages'] == 2
    
    # Test with mood filter
    response = client.get('/api/tracking/journals?mood=happy', headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert all(j['mood'] == 'happy' for j in data['items'])
    
    # Test with date range
    start_date = (datetime.now(timezone.utc) - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    response = client.get(f'/api/tracking/journals?start_date={start_date}', headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) <= 6  # Only journals from last 5 days

def test_create_journal(client, auth_tokens):
    """Test creating a new journal entry"""
    user = User.query.first()
    
    # Test with valid data
    data = {
        'title': 'Test Journal',
        'content': 'Test Content',
        'mood': 'happy'
    }
    response = client.post('/api/tracking/journals', 
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Test Journal'
    assert data['content'] == 'Test Content'
    assert data['mood'] == 'happy'
    
    # Test with missing required field
    data = {'title': 'Test Journal'}
    response = client.post('/api/tracking/journals',
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 400

def test_update_journal(client, auth_tokens):
    """Test updating a journal entry"""
    user = User.query.first()
    
    # Create a test journal
    journal = Journal(
        id='test-journal',
        user_id=user.id,
        title='Original Title',
        content='Original Content',
        mood='happy'
    )
    db.session.add(journal)
    db.session.commit()
    
    # Test updating fields
    data = {
        'title': 'Updated Title',
        'content': 'Updated Content',
        'mood': 'sad'
    }
    response = client.put(f'/api/tracking/journals/{journal.id}',
                         json=data,
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Updated Title'
    assert data['content'] == 'Updated Content'
    assert data['mood'] == 'sad'
    
    # Test updating non-existent journal
    response = client.put('/api/tracking/journals/non-existent',
                         json=data,
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 404

def test_delete_journal(client, auth_tokens):
    """Test deleting a journal entry"""
    user = User.query.first()
    
    # Create a test journal
    journal = Journal(
        id='test-journal',
        user_id=user.id,
        title='Test Title',
        content='Test Content'
    )
    db.session.add(journal)
    db.session.commit()
    
    # Test deleting journal
    response = client.delete(f'/api/tracking/journals/{journal.id}',
                           headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    
    # Verify journal is deleted
    deleted_journal = db.session.get(Journal, journal.id)
    assert deleted_journal is None

def test_weight_logs(client, auth_tokens):
    """Test weight log endpoints"""
    user = User.query.first()
    
    # Test creating weight log
    data = {
        'weight': 75.5,
        'date': datetime.now(timezone.utc).isoformat(),
        'notes': 'Test weight log'
    }
    response = client.post('/api/tracking/weight-logs',
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['weight'] == 75.5
    assert data['notes'] == 'Test weight log'
    
    # Test invalid weight
    data = {'weight': -1}
    response = client.post('/api/tracking/weight-logs',
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 400
    
    # Test getting weight logs
    response = client.get('/api/tracking/weight-logs',
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) > 0

def test_progress_photos(client, auth_tokens):
    """Test progress photo endpoints"""
    user = User.query.first()
    
    # Test creating progress photo
    data = {
        'photo_url': 'https://example.com/photo.jpg',
        'category': 'front',
        'date': datetime.now(timezone.utc).isoformat(),
        'notes': 'Test progress photo'
    }
    response = client.post('/api/tracking/progress-photos',
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['photo_url'] == 'https://example.com/photo.jpg'
    assert data['category'] == 'front'
    
    # Test invalid category
    data = {'photo_url': 'https://example.com/photo.jpg', 'category': 'invalid'}
    response = client.post('/api/tracking/progress-photos',
                          json=data,
                          headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 400
    
    # Test getting progress photos
    response = client.get('/api/tracking/progress-photos',
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) > 0

def test_analytics(client, auth_tokens):
    """Test analytics endpoints"""
    user = User.query.first()
    
    # Create test data
    # Weight logs
    weight_logs = [
        WeightLog(
            id=f'weight-{i}',
            user_id=user.id,
            weight=75.0 + i,
            date=datetime.now(timezone.utc) - timedelta(days=i)
        ) for i in range(5)
    ]
    db.session.add_all(weight_logs)
    
    # Journal entries with mood
    journals = [
        Journal(
            id=f'journal-{i}',
            user_id=user.id,
            title=f'Test Journal {i}',
            content=f'Test Content {i}',
            mood='happy' if i % 2 == 0 else 'sad',
            created_at=datetime.now(timezone.utc) - timedelta(days=i)
        ) for i in range(5)
    ]
    db.session.add_all(journals)
    
    # Progress photos
    photos = [
        ProgressPhoto(
            id=f'photo-{i}',
            user_id=user.id,
            photo_url=f'https://example.com/photo{i}.jpg',
            category='front' if i % 2 == 0 else 'side',
            date=datetime.now(timezone.utc) - timedelta(days=i)
        ) for i in range(5)
    ]
    db.session.add_all(photos)
    db.session.commit()
    
    # Test weight trend
    response = client.get('/api/tracking/analytics/weight-trend',
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['weight_data']) == 5
    assert data['start_weight'] == 79.0  # Most recent weight
    assert data['current_weight'] == 75.0  # Oldest weight
    assert data['weight_change'] == -4.0  # Weight decreased by 4.0
    
    # Test mood trend
    response = client.get('/api/tracking/analytics/mood-trend',
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['mood_data']) == 5
    assert data['mood_distribution']['happy'] == 3
    assert data['mood_distribution']['sad'] == 2
    
    # Test progress summary
    response = client.get('/api/tracking/analytics/progress-summary',
                         headers={'Authorization': f'Bearer {auth_tokens["access_token"]}'})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['category_photos']['front']) == 3
    assert len(data['category_photos']['side']) == 2
    assert data['total_photos'] == 5
    assert data['weight_stats']['total_measurements'] == 5 
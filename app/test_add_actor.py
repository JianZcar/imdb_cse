import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful actor creation
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_create_actor_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the POST request to create an actor
    response = client.post('/actors', json={
        'first_name': 'Leonardo',
        'last_name': 'DiCaprio'
    })

    # Assert the response
    assert response.status_code == 201
    assert b'Actor created successfully' in response.data  # Success message

# Test for missing data
@patch('main.authenticate')  # Mock the authentication
def test_create_actor_missing_data(mock_auth, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Simulate the POST request with missing data
    response = client.post('/actors', json={
        'first_name': 'Leonardo'  # Missing last_name
    })

    # Assert the response
    assert response.status_code == 400
    assert b'First name and last name are required' in response.data  # Error message

# Test for authentication failure
@patch('main.authenticate')  # Mock the authentication
def test_create_actor_auth_failure(mock_auth, client):
    # Mock authentication to fail
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the POST request to create an actor
    response = client.post('/actors', json={
        'first_name': 'Leonardo',
        'last_name': 'DiCaprio'
    })

    # Assert the response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data  # Error message

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_create_actor_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the POST request to create an actor
    response = client.post('/actors', json={
        'first_name': 'Leonardo',
        'last_name': 'DiCaprio'
    })

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while creating the actor' in response.data  # Error message

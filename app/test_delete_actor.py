import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful actor deletion
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_actor_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate actor existence
    mock_cursor.fetchone.return_value = {'actor_id': 1}

    # Simulate the DELETE request to delete an actor
    response = client.delete('/actors/1')

    # Assert the response
    assert response.status_code == 200
    assert b'Actor deleted successfully' in response.data

# Test for actor not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_actor_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # Actor does not exist
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the DELETE request to delete an actor
    response = client.delete('/actors/999')

    # Assert the response
    assert response.status_code == 404
    assert b'Actor not found' in response.data

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_actor_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the DELETE request to delete an actor
    response = client.delete('/actors/1')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while deleting the actor' in response.data

# Test for unauthorized access
@patch('main.authenticate')  # Mock the authentication
def test_delete_actor_unauthorized(mock_auth, client):
    # Mock authentication to fail
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the DELETE request
    response = client.delete('/actors/1')

    # Assert the response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

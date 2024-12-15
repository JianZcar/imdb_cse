import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successful token deletion
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_token_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1, 'role': 0}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate token existence
    mock_cursor.fetchone.return_value = {'api_key': 'dummy_key'}

    # Simulate the DELETE request to delete a token
    response = client.delete('/tokens/1')

    # Assert the response
    assert response.status_code == 200
    assert response.json == {'message': 'Token deleted successfully'}

# Test for token not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_token_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1, 'role': 0}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate token not found
    mock_cursor.fetchone.return_value = None

    # Simulate the DELETE request to delete a non-existent token
    response = client.delete('/tokens/999')

    # Assert the response
    assert response.status_code == 404
    assert response.json == {'message': 'Token not found for this user'}

# Test for unauthorized access
@patch('main.authenticate')  # Mock the authentication
def test_delete_token_unauthorized(mock_auth, client):
    # Mock authentication to fail
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the DELETE request
    response = client.delete('/tokens/1')

    # Assert the response
    assert response.status_code == 401
    assert response.json == {'success': False, 'message': 'Unauthorized'}

# Test for database error during token deletion
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_token_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1, 'role': 0}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the DELETE request
    response = client.delete('/tokens/1')

    # Assert the response
    assert response.status_code == 500
    assert response.json == {'error': 'An error occurred while deleting the token'}

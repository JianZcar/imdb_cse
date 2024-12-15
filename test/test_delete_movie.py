import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful movie deletion
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_movie_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie existence
    mock_cursor.fetchone.return_value = {'movie_id': 1}

    # Simulate the DELETE request
    response = client.delete('/movies/1')

    # Assert the response
    assert response.status_code == 200
    assert b'Movie deleted successfully' in response.data

# Test for movie not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_movie_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # Movie does not exist
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the DELETE request
    response = client.delete('/movies/999')

    # Assert the response
    assert response.status_code == 404
    assert b'Movie not found' in response.data

# Test for database error during deletion
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_delete_movie_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the DELETE request
    response = client.delete('/movies/1')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while deleting the movie' in response.data

# Test for unauthorized access
@patch('main.authenticate')  # Mock the authentication
def test_delete_movie_unauthorized(mock_auth, client):
    # Mock authentication to fail
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the DELETE request
    response = client.delete('/movies/1')

    # Assert the response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

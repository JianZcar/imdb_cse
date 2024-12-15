import pytest
from unittest.mock import patch, MagicMock
from main import app  # Assuming your Flask app is named 'main'

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully deleting a genre
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_delete_genre_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate that the genre exists in the database
    mock_cursor.fetchone.return_value = {'movie_genres_type': 'Action'}  # Genre exists
    mock_cursor.execute.return_value = None  # Simulate the DELETE queries running without errors

    # Simulate the DELETE request to delete the genre 'Action'
    response = client.delete('/genres/Action')

    # Assert the response
    assert response.status_code == 200
    assert b'Genre deleted successfully' in response.data  # Check for success message

# Test for attempting to delete a non-existing genre
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_delete_genre_not_found(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate that the genre does not exist in the database
    mock_cursor.fetchone.return_value = None  # Genre does not exist

    # Simulate the DELETE request to delete a non-existing genre
    response = client.delete('/genres/NonExistingGenre')

    # Assert the response
    assert response.status_code == 404
    assert b'Genre not found' in response.data  # Check for the error message

# Test for database error during genre deletion
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_delete_genre_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database error (raise exception during query execution)
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the DELETE request to delete the genre 'Action'
    response = client.delete('/genres/Action')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching the genre' in response.data  # Check for the error message

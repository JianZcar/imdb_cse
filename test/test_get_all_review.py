import pytest
from unittest.mock import patch, MagicMock
from main import app  # Assuming your Flask app is named 'main'

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully fetching a review
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_specific_review_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a review being fetched from the database
    mock_cursor.fetchone.return_value = {
        'review_id': 1, 'movie_id': 101, 'star_rating': 5, 'review_text': 'Great movie!',
        'movie_title': 'Movie 1', 'username': 'user1'
    }

    # Simulate the GET request to fetch a specific review
    response = client.get('/reviews/1')  # Get review with ID 1

    # Assert the response
    assert response.status_code == 200
    assert b'Great movie!' in response.data  # Check for review text
    assert b'Movie 1' in response.data  # Check for movie title
    assert b'user1' in response.data  # Check for username

# Test for review not found
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_specific_review_not_found(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no review found in the database for the provided review_id
    mock_cursor.fetchone.return_value = None  # No review found

    # Simulate the GET request to fetch a specific review
    response = client.get('/reviews/999')  # Get review with non-existent ID

    # Assert the response
    assert response.status_code == 404
    assert b'Review not found' in response.data  # Check for not found message

# Test for authentication failure (not an admin)
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_specific_review_auth_failure(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate failure for non-admin
    mock_authenticate.return_value = {'success': False, 'message': 'Unauthorized'}, 403

    # Simulate the GET request to fetch a specific review
    response = client.get('/reviews/1')  # Get review with ID 1

    # Assert the response
    assert response.status_code == 403
    assert b'Unauthorized' in response.data  # Check for authentication failure message

# Test for database error
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_specific_review_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database error (raise exception during query execution)
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the GET request to fetch a specific review
    response = client.get('/reviews/1')  # Get review with ID 1

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching the review' in response.data  # Check for error message

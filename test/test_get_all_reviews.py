import pytest
from unittest.mock import patch, MagicMock
from main import app  # Assuming your Flask app is named 'main'

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully fetching reviews
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_all_reviews_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the reviews data
    mock_cursor.fetchall.return_value = [
        {'review_id': 1, 'movie_id': 101, 'star_rating': 5, 'review_text': 'Great movie!', 'movie_title': 'Movie 1', 'username': 'user1'},
        {'review_id': 2, 'movie_id': 102, 'star_rating': 4, 'review_text': 'Good movie!', 'movie_title': 'Movie 2', 'username': 'user2'}
    ]  # Simulate two reviews in the database

    # Simulate the GET request to fetch all reviews
    response = client.get('/reviews')

    # Assert the response
    assert response.status_code == 200
    assert b'Great movie!' in response.data  # Check for review text
    assert b'Good movie!' in response.data  # Check for review text
    assert b'Movie 1' in response.data  # Check for movie title
    assert b'Movie 2' in response.data  # Check for movie title

# Test for no reviews found
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_all_reviews_no_reviews(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no reviews in the database
    mock_cursor.fetchall.return_value = []  # No reviews

    # Simulate the GET request to fetch all reviews
    response = client.get('/reviews')

    # Assert the response
    assert response.status_code == 404
    assert b'No reviews found' in response.data  # Check for no reviews message

# Test for authentication failure (not an admin)
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_all_reviews_auth_failure(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate failure for non-admin
    mock_authenticate.return_value = {'success': False, 'message': 'Unauthorized'}, 403

    # Simulate the GET request to fetch all reviews
    response = client.get('/reviews')

    # Assert the response
    assert response.status_code == 403
    assert b'Unauthorized' in response.data  # Check for authentication failure message

# Test for database error
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_all_reviews_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success for admin
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database error (raise exception during query execution)
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the GET request to fetch all reviews
    response = client.get('/reviews')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching reviews' in response.data  # Check for error message

import pytest
from unittest.mock import patch, MagicMock
from main import app  # Assuming your Flask app is named 'main'

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully retrieving user reviews
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_user_reviews_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the reviews data
    mock_cursor.fetchall.return_value = [
        {'review_id': 1, 'movie_id': 1, 'star_rating': 5, 'review_text': 'Great movie!', 'movie_title': 'Inception'},
        {'review_id': 2, 'movie_id': 2, 'star_rating': 4, 'review_text': 'Good movie.', 'movie_title': 'The Matrix'}
    ]

    # Simulate the GET request to fetch user reviews
    response = client.get('/profile/reviews')

    # Assert the response
    assert response.status_code == 200
    assert b'Great movie!' in response.data  # Check for review text
    assert b'The Matrix' in response.data  # Check for movie title

# Test for no reviews found
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_user_reviews_no_reviews(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no reviews found (empty result)
    mock_cursor.fetchall.return_value = []

    # Simulate the GET request to fetch user reviews
    response = client.get('/profile/reviews')

    # Assert the response
    assert response.status_code == 404
    assert b'No reviews found for this user' in response.data  # Check for no reviews message

# Test for authentication failure
@patch('main.authenticate')  # Mock the authenticate function
def test_get_user_reviews_auth_failed(mock_authenticate, client):
    # Mock authentication response to simulate failure
    mock_authenticate.return_value = {'success': False, 'message': 'Authentication failed'}, 401

    # Simulate the GET request to fetch user reviews
    response = client.get('/profile/reviews')

    # Assert the response
    assert response.status_code == 401
    assert b'Authentication failed' in response.data  # Check for authentication failure message

# Test for database error
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_user_reviews_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database error (raise exception during query execution)
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the GET request to fetch user reviews
    response = client.get('/profile/reviews')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching reviews' in response.data  # Check for error message

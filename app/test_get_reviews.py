import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful retrieval of reviews
@patch('main.get_db_connection')  # Mock the database connection
def test_get_reviews_success(mock_db, client):
    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate reviews for a movie
    mock_cursor.fetchall.return_value = [
        {'review_id': 1, 'star_rating': 5, 'review_text': 'Excellent movie!'},
        {'review_id': 2, 'star_rating': 4, 'review_text': 'Very good movie, but a bit slow.'}
    ]

    # Simulate the GET request to fetch reviews for a movie
    response = client.get('/movies/1/reviews')

    # Assert the response
    assert response.status_code == 200
    assert b'Reviews retrieved successfully' in response.data
    assert b'Excellent movie!' in response.data
    assert b'Very good movie, but a bit slow.' in response.data

# Test for no reviews found
@patch('main.get_db_connection')  # Mock the database connection
def test_get_reviews_no_reviews(mock_db, client):
    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no reviews for the movie
    mock_cursor.fetchall.return_value = []

    # Simulate the GET request to fetch reviews for a movie
    response = client.get('/movies/1/reviews')

    # Assert the response
    assert response.status_code == 404
    assert b'No reviews found for this movie' in response.data

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
def test_get_reviews_db_error(mock_db, client):
    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the GET request to fetch reviews for a movie
    response = client.get('/movies/1/reviews')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching reviews' in response.data

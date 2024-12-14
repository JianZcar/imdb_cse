import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful review addition
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_review_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie existence
    mock_cursor.fetchone.return_value = {'movie_id': 1}

    # Simulate the POST request to add a review
    response = client.post('/movies/1/reviews', json={
        'star_rating': 8.0,
        'review_text': 'Great movie!'
    })

    # Assert the response
    assert response.status_code == 201
    assert b'Review added successfully' in response.data

# Test for missing required fields
@patch('main.authenticate')  # Mock the authentication
def test_add_review_missing_fields(mock_auth, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1}, 200)

    # Simulate the POST request with missing fields (no 'star_rating')
    response = client.post('/movies/1/reviews', json={
        'review_text': 'Great movie!'
    })

    # Assert the response
    assert response.status_code == 400
    assert b"Missing required fields: 'star_rating' and 'review_text'" in response.data

# Test for invalid star rating
@patch('main.authenticate')  # Mock the authentication
def test_add_review_invalid_star_rating(mock_auth, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1}, 200)

    # Simulate the POST request with an invalid star_rating (greater than 10)
    response = client.post('/movies/1/reviews', json={
        'star_rating': 11.0,
        'review_text': 'Great movie!'
    })

    # Assert the response
    assert response.status_code == 400
    assert b"Invalid 'star_rating'. It must be between 0.0 and 10.0" in response.data

# Test for movie not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_review_movie_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1}, 200)

    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie not found
    mock_cursor.fetchone.return_value = None

    # Simulate the POST request to add a review
    response = client.post('/movies/999/reviews', json={
        'star_rating': 8.0,
        'review_text': 'Great movie!'
    })

    # Assert the response
    assert response.status_code == 404
    assert b'Movie with ID 999 not found' in response.data

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_review_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'user_id': 1}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the POST request to add a review
    response = client.post('/movies/1/reviews', json={
        'star_rating': 8.0,
        'review_text': 'Great movie!'
    })

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while adding the review' in response.data

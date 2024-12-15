import pytest
from unittest.mock import patch, MagicMock
from main import app  # Assuming your Flask app is named 'main'

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully updating a review
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_update_review_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the review data
    mock_cursor.fetchone.return_value = {'user_id': 1}  # Simulate review belonging to the authenticated user

    # Simulate the PUT request to update the review
    data = {'star_rating': 4, 'review_text': 'Great movie!'}
    response = client.put('/profile/reviews/1', json=data)

    # Assert the response
    assert response.status_code == 200
    assert b'Review updated successfully' in response.data  # Check for success message

# Test for missing star rating or review text
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_update_review_missing_data(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the PUT request with missing review text
    data = {'star_rating': 4}
    response = client.put('/profile/reviews/1', json=data)

    # Assert the response
    assert response.status_code == 400
    assert b'Star rating and review text are required' in response.data  # Check for missing data error message

# Test for review not found
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_update_review_not_found(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the review not found
    mock_cursor.fetchone.return_value = None  # Simulate review not found

    # Simulate the PUT request to update the review
    data = {'star_rating': 4, 'review_text': 'Great movie!'}
    response = client.put('/profile/reviews/1', json=data)

    # Assert the response
    assert response.status_code == 404
    assert b'Review not found' in response.data  # Check for review not found message

# Test for unauthorized update (trying to update someone else's review)
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_update_review_unauthorized(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the review data (review belongs to another user)
    mock_cursor.fetchone.return_value = {'user_id': 2}  # Simulate review belonging to user 2

    # Simulate the PUT request to update the review
    data = {'star_rating': 4, 'review_text': 'Great movie!'}
    response = client.put('/profile/reviews/1', json=data)

    # Assert the response
    assert response.status_code == 403
    assert b'You can only update your own reviews' in response.data  # Check for unauthorized message

# Test for database error
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_update_review_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database error (raise exception during query execution)
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the PUT request to update the review
    data = {'star_rating': 4, 'review_text': 'Great movie!'}
    response = client.put('/profile/reviews/1', json=data)

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while updating the review' in response.data  # Check for error message

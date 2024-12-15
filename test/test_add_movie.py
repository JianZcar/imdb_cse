import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import your Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully adding a movie
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_movie_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200
    
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate the movie data
    data = {'title': 'Inception'}
    
    # Simulate the movie insertion (mock lastrowid for the new movie)
    mock_cursor.lastrowid = 1  # Simulate the new movie ID
    
    # Simulate the POST request to add a movie
    response = client.post('/movies', json=data)
    
    # Check if the response status code is 201 (created)
    assert response.status_code == 201
    assert b'Movie added successfully' in response.data  # Check for success message
    assert b'movie_id' in response.data  # Check for the movie ID in the response

# Test for failed authentication
@patch('main.authenticate')  # Mock the authenticate function
def test_add_movie_auth_failed(mock_authenticate, client):
    # Mock authentication response to simulate failure
    mock_authenticate.return_value = {'success': False, 'message': 'Authentication failed'}, 401
    
    # Simulate the movie data
    data = {'title': 'Inception'}
    
    # Simulate the POST request to add a movie
    response = client.post('/movies', json=data)
    
    # Check if the response status code is 401 (unauthorized)
    assert response.status_code == 401
    assert b'Authentication failed' in response.data  # Check for the failure message

# Test for missing title in the request
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_movie_missing_title(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200
    
    # Simulate missing title in the movie data
    data = {}
    
    # Simulate the POST request to add a movie
    response = client.post('/movies', json=data)
    
    # Check if the response status code is 400 (bad request)
    assert response.status_code == 400
    assert b'Missing required fields: title' in response.data  # Check for the error message

# Test for database error
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_movie_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200
    
    # Mock the database cursor to raise an exception (simulate a database error)
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database error")
    
    # Simulate the movie data
    data = {'title': 'Inception'}
    
    # Simulate the POST request to add a movie
    response = client.post('/movies', json=data)
    
    # Check if the response status code is 500 (internal server error)
    assert response.status_code == 500
    assert b'An error occurred while adding the movie' in response.data  # Check for the error message

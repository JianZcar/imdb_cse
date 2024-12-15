import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successfully adding a new genre
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_genre_success(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the genre data
    data = {'movie_genres_type': 'Action'}

    # Simulate the genre not already existing (empty result from SELECT query)
    mock_cursor.fetchone.return_value = None  # Ensure genre doesn't exist in the DB

    # Simulate the genre insertion (mock commit for new genre)
    mock_cursor.lastrowid = 1  # Simulate the new genre ID

    # Simulate the POST request to add a genre
    response = client.post('/genres', json=data)

    # Assert the response
    assert response.status_code == 201
    assert b'Genre added successfully' in response.data  # Check for success message

# Test for failed authentication
@patch('main.authenticate')  # Mock the authenticate function
def test_add_genre_auth_failed(mock_authenticate, client):
    # Mock authentication response to simulate failure
    mock_authenticate.return_value = {'success': False, 'message': 'Authentication failed'}, 401
    
    # Simulate the genre data
    data = {'movie_genres_type': 'Action'}
    
    # Simulate the POST request to add a genre
    response = client.post('/genres', json=data)
    
    # Assert the response
    assert response.status_code == 401
    assert b'Authentication failed' in response.data  # Check for failure message

# Test for missing genre type in the request
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_genre_missing_type(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200
    
    # Simulate missing genre type in the data
    data = {}
    
    # Simulate the POST request to add a genre
    response = client.post('/genres', json=data)
    
    # Assert the response
    assert response.status_code == 400
    assert b'Genre type is required' in response.data  # Check for the error message

# Test for genre already exists
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_genre_already_exists(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200
    
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate the genre already existing in the database
    mock_cursor.fetchone.return_value = {'movie_genres_type': 'Action'}
    
    # Simulate the POST request to add an existing genre
    data = {'movie_genres_type': 'Action'}
    
    # Simulate the POST request to add a genre
    response = client.post('/genres', json=data)
    
    # Assert the response
    assert response.status_code == 400
    assert b'Genre already exists' in response.data  # Check for the error message

# Test for database error while adding a genre
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_add_genre_db_error(mock_db, mock_authenticate, client):
    # Mock authentication response to simulate success
    mock_authenticate.return_value = {'success': True}, 200
    
    # Mock the database cursor to raise an exception (simulate a database error)
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database error")
    
    # Simulate the genre data
    data = {'movie_genres_type': 'Action'}
    
    # Simulate the POST request to add a genre
    response = client.post('/genres', json=data)
    
    # Assert the response
    assert response.status_code == 500
    assert b'Error occurred while adding the genre' in response.data  # Check for the error message

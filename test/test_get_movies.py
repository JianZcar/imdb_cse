import pytest
from unittest.mock import patch, MagicMock
from main import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully retrieving movies
@patch('main.get_db_connection')  # Mock the database connection
def test_get_movies_success(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate some movies being returned from the database
    mock_cursor.fetchall.return_value = [
        {'movie_id': 1, 'movie_title': 'Inception'},
        {'movie_id': 2, 'movie_title': 'The Dark Knight'}
    ]
    
    # Simulate the GET request to /movies
    response = client.get('/movies')
    
    # Check if the response status code is 200 (success)
    assert response.status_code == 200
    assert b'movies' in response.data
    assert b'Inception' in response.data
    assert b'The Dark Knight' in response.data

# Test for when no movies are found (if the database returns an empty result)
@patch('main.get_db_connection')  # Mock the database connection
def test_get_movies_no_movies(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate no movies found in the database
    mock_cursor.fetchall.return_value = []  # Empty list, no movies
    
    # Simulate the GET request to /movies
    response = client.get('/movies')
    
    # Check if the response status code is 404 (not found)
    assert response.status_code == 404
    assert b'No movies found' in response.data

# Test for internal server error
@patch('main.get_db_connection')  # Mock the database connection
def test_get_movies_internal_error(mock_db, client):
    # Mock the database cursor to raise an exception (simulate an error)
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchall.side_effect = Exception("Database error")
    
    # Simulate the GET request to /movies
    response = client.get('/movies')
    
    # Check if the response status code is 500 (internal server error)
    assert response.status_code == 500
    assert b'Error occurred while fetching movies' in response.data

import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for fetching actors successfully for a movie
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_actors_success(mock_db, client):
    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate actors for the movie
    mock_cursor.fetchall.return_value = [
        {'actor_id': 1, 'first_name': 'Robert', 'last_name': 'Downey Jr.'},
        {'actor_id': 2, 'first_name': 'Chris', 'last_name': 'Evans'}
    ]
    
    # Simulate the GET request to fetch actors for movie with ID 1
    response = client.get('/movies/1/actors')
    
    # Assert the response
    assert response.status_code == 200
    
    # Parse the JSON response
    actors_data = response.get_json()['actors']
    
    # Check if the full names are in the response
    assert any(actor['first_name'] == 'Robert' and actor['last_name'] == 'Downey Jr.' for actor in actors_data)
    assert any(actor['first_name'] == 'Chris' and actor['last_name'] == 'Evans' for actor in actors_data)

# Test for no actors found for a movie
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_actors_no_actors(mock_db, client):
    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no actors for the movie
    mock_cursor.fetchall.return_value = []

    # Simulate the GET request to fetch actors for movie with ID 1
    response = client.get('/movies/1/actors')

    # Assert the response
    assert response.status_code == 404
    assert b'No actors found for this movie' in response.data

# Test for database error while fetching actors
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_actors_db_error(mock_db, client):
    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate a database exception
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the GET request to fetch actors for movie with ID 1
    response = client.get('/movies/1/actors')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching actors' in response.data

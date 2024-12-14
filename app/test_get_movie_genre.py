import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful genre retrieval
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_genres_success(mock_db, client):
    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie having genres
    mock_cursor.fetchall.return_value = [{'movie_genres_type': 'Action'}, {'movie_genres_type': 'Adventure'}]

    # Simulate the GET request to fetch genres for a movie
    response = client.get('/movies/1/genres')

    # Assert the response
    assert response.status_code == 200
    assert b'Action' in response.data
    assert b'Adventure' in response.data

# Test for no genres found
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_genres_no_genres(mock_db, client):
    # Mock the database connection
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie having no genres
    mock_cursor.fetchall.return_value = []

    # Simulate the GET request to fetch genres for a movie
    response = client.get('/movies/1/genres')

    # Assert the response
    assert response.status_code == 404
    assert b'No genres found for this movie' in response.data

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_genres_db_error(mock_db, client):
    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the GET request to fetch genres for a movie
    response = client.get('/movies/1/genres')

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while fetching genres' in response.data

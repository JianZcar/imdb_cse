import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successful retrieval of genres
@patch('main.get_db_connection')  # Mock the database connection
def test_genres_success(mock_db, client):
    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate database rows returned by the query
    mock_cursor.fetchall.return_value = [
        {'movie_genres_type': 'Action'},
        {'movie_genres_type': 'Comedy'},
        {'movie_genres_type': 'Drama'}
    ]

    # Simulate the GET request to fetch genres
    response = client.get('/genres')

    # Assert the response
    assert response.status_code == 200
    assert response.json == {'genres': ['Action', 'Comedy', 'Drama']}

# Test for empty genres table
@patch('main.get_db_connection')  # Mock the database connection
def test_genres_empty(mock_db, client):
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate an empty database table
    mock_cursor.fetchall.return_value = []

    response = client.get('/genres')

    # Assert the response
    assert response.status_code == 200
    assert response.json == {'genres': []}

# Test for database error during fetching genres
@patch('main.get_db_connection')  # Mock the database connection
def test_genres_db_error(mock_db, client):
    # Simulate a database connection error
    mock_db.side_effect = Exception("Database connection failed")

    response = client.get('/genres')

    # Assert the response
    assert response.status_code == 500
    assert response.json == {'error': 'Error occurred while fetching genres'}

import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Test for successful retrieval of a genre with movies
@patch('main.get_db_connection')  # Mock the database connection
def test_genre_by_type_success(mock_db, client):
    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the genre query result
    mock_cursor.fetchone.return_value = {'movie_genres_type': 'Action'}

    # Simulate the movies associated with the genre
    mock_cursor.fetchall.return_value = [
        {'movie_id': 1, 'movie_title': 'Action Movie 1'},
        {'movie_id': 2, 'movie_title': 'Action Movie 2'}
    ]

    # Simulate the GET request to fetch movies for the genre 'Action'
    response = client.get('/genres/Action')

    # Assert the response
    assert response.status_code == 200
    assert response.json == {'genre': {
        'movie_genres_type': 'Action',
        'movies': [
            {'movie_id': 1, 'movie_title': 'Action Movie 1'},
            {'movie_id': 2, 'movie_title': 'Action Movie 2'}
        ]
    }}

# Test for genre not found
@patch('main.get_db_connection')  # Mock the database connection
def test_genre_by_type_not_found(mock_db, client):
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the genre query returning None (genre not found)
    mock_cursor.fetchone.return_value = None

    # Simulate the GET request to fetch a non-existing genre 'Fantasy'
    response = client.get('/genres/Fantasy')

    # Assert the response
    assert response.status_code == 404
    assert response.json == {'error': 'Genre not found'}

# Test for database error during fetching genre details
@patch('main.get_db_connection')  # Mock the database connection
def test_genre_by_type_db_error(mock_db, client):
    # Simulate a database connection error
    mock_db.side_effect = Exception("Database connection failed")

    response = client.get('/genres/Action')

    # Assert the response
    assert response.status_code == 500
    assert response.data.decode() == "Error occurred while fetching genre details"

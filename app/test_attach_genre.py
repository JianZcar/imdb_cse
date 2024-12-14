import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful genre addition to a movie
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_success(mock_auth, mock_db, client):
    # Mock authentication to succeed and ensure the user has role 1 (admin)
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie existence and genre existence
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        {'movie_genres_type': 'Action'},  # Genre exists
        None  # No existing association for this genre (will be inserted)
    ]

    # Simulate the POST request to add genre to the movie
    response = client.post('/movies/1/genres', json={
        'movie_genres_type': 'Action'
    })

    # Assert the response
    assert response.status_code == 201
    assert b'Genre added to the movie successfully' in response.data

# Test for movie not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_movie_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie not found
    mock_cursor.fetchone.side_effect = [None, {'movie_genres_type': 'Action'}]

    # Simulate the POST request to add genre to a non-existent movie
    response = client.post('/movies/999/genres', json={
        'movie_genres_type': 'Action'
    })

    # Assert the response
    assert response.status_code == 404
    assert b'Movie not found' in response.data

# Test for genre not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_genre_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie and genre existence, with genre not found
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        None  # Genre not found
    ]

    # Simulate the POST request to add a non-existent genre
    response = client.post('/movies/1/genres', json={
        'movie_genres_type': 'Sci-Fi'
    })

    # Assert the response
    assert response.status_code == 404
    assert b'Genre not found' in response.data

# Test for genre already associated with the movie
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_already_associated(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie and genre existence, with existing association
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        {'movie_genres_type': 'Action'},  # Genre exists
        {'movies_movie_id': 1, 'ref_movie_genres_movie_genres_type': 'Action'}  # Already associated
    ]

    # Simulate the POST request to add genre that is already associated
    response = client.post('/movies/1/genres', json={
        'movie_genres_type': 'Action'
    })

    # Assert the response
    assert response.status_code == 200
    assert b'Genre already associated with this movie' in response.data

# Test for unauthorized access
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_unauthorized(mock_auth, client):
    # Mock authentication to fail (e.g., user is not admin)
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the POST request
    response = client.post('/movies/1/genres', json={
        'movie_genres_type': 'Action'
    })

    # Assert the response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

# Test for database error during genre addition
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_genre_to_movie_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the POST request to add genre to the movie
    response = client.post('/movies/1/genres', json={
        'movie_genres_type': 'Action'
    })

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while adding genre to movie' in response.data

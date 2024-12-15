import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_success(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie, actor, and no existing association
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        {'actor_id': 1, 'first_name': 'Robert', 'last_name': 'Downey Jr.'},  # Actor exists
        None  # No existing association
    ]

    # Simulate the POST request to add actor to the movie
    response = client.post('/movies/1/actors', json={
        'actor_id': 1
    })

    # Assert the response
    assert response.status_code == 201
    assert b'Actor added to the movie successfully' in response.data

# Test for movie not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_movie_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie not found
    mock_cursor.fetchone.side_effect = [None, {'actor_id': 1, 'first_name': 'Robert', 'last_name': 'Downey Jr.'}]

    # Simulate the POST request to add actor to a non-existent movie
    response = client.post('/movies/999/actors', json={
        'actor_id': 1
    })

    # Assert the response
    assert response.status_code == 404
    assert b'Movie not found' in response.data

# Test for actor not found
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_actor_not_found(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie and actor existence, with actor not found
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        None  # Actor not found
    ]

    # Simulate the POST request to add a non-existent actor
    response = client.post('/movies/1/actors', json={
        'actor_id': 999
    })

    # Assert the response
    assert response.status_code == 404
    assert b'Actor not found' in response.data

# Test for actor already associated with the movie
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_already_associated(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection and cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate movie and actor existence, with existing association
    mock_cursor.fetchone.side_effect = [
        {'movie_id': 1},  # Movie exists
        {'actor_id': 1, 'first_name': 'Robert', 'last_name': 'Downey Jr.'},  # Actor exists
        {'movies_movie_id': 1, 'actors_actor_id': 1}  # Actor already associated
    ]

    # Simulate the POST request to add actor that is already associated
    response = client.post('/movies/1/actors', json={
        'actor_id': 1
    })

    # Assert the response
    assert response.status_code == 200
    assert b'Actor already associated with this movie' in response.data

# Test for unauthorized access
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_unauthorized(mock_auth, client):
    # Mock authentication to fail (e.g., user is not admin)
    mock_auth.return_value = ({'success': False, 'message': 'Unauthorized'}, 401)

    # Simulate the POST request
    response = client.post('/movies/1/actors', json={
        'actor_id': 1
    })

    # Assert the response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data

# Test for database error during actor addition
@patch('main.get_db_connection')  # Mock the database connection
@patch('main.authenticate')  # Mock the authentication
def test_add_actor_to_movie_db_error(mock_auth, mock_db, client):
    # Mock authentication to succeed
    mock_auth.return_value = ({'success': True, 'role': 1}, 200)

    # Mock the database connection to raise an exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Database error")
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the POST request to add actor to the movie
    response = client.post('/movies/1/actors', json={
        'actor_id': 1
    })

    # Assert the response
    assert response.status_code == 500
    assert b'An error occurred while adding actor to movie' in response.data

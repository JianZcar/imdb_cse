import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully fetching actor details by ID
@patch('main.get_db_connection')  # Mock the database connection
def test_actor_by_id_success(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate actor details being returned
    mock_cursor.fetchone.side_effect = [
        {'actor_id': 1, 'first_name': 'Leonardo', 'last_name': 'DiCaprio'},  # Actor details
    ]

    # Simulate movies the actor has appeared in
    mock_cursor.fetchall.return_value = [
        {'movie_id': 1, 'movie_title': 'Inception'},
        {'movie_id': 2, 'movie_title': 'Titanic'}
    ]

    # Simulate the GET request to /actors/1
    response = client.get('/actors/1')

    # Assert the response
    assert response.status_code == 200
    assert b'Leonardo' in response.data  # Actor first name
    assert b'DiCaprio' in response.data  # Actor last name
    assert b'Inception' in response.data  # Movie title
    assert b'Titanic' in response.data  # Movie title

# Test for actor not found
@patch('main.get_db_connection')  # Mock the database connection
def test_actor_by_id_not_found(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no actor found
    mock_cursor.fetchone.return_value = None  # No actor details

    # Simulate the GET request to /actors/999 (nonexistent actor)
    response = client.get('/actors/999')

    # Assert the response
    assert response.status_code == 404
    assert b'Actor not found' in response.data  # Error message

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
def test_actor_by_id_db_error(mock_db, client):
    # Mock the database cursor to raise an exception (simulate a database error)
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database error")

    # Simulate the GET request to /actors/1
    response = client.get('/actors/1')

    # Assert the response
    assert response.status_code == 500
    assert b"Error occurred while fetching actor details" in response.data  # Error message

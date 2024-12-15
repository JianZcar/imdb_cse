import pytest
from unittest.mock import patch, MagicMock
from main import app  # Import your Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully fetching actors
@patch('main.get_db_connection')  # Mock the database connection
def test_actors_success(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate actor data being returned
    mock_cursor.fetchall.return_value = [
        {'actor_id': 1, 'first_name': 'Leonardo', 'last_name': 'DiCaprio'},
        {'actor_id': 2, 'first_name': 'Brad', 'last_name': 'Pitt'}
    ]
    
    # Simulate the GET request to /actors
    response = client.get('/actors')
    
    # Check if the response status code is 200 (success)
    assert response.status_code == 200
    assert b'Leonardo' in response.data  # Check if actor data is in the response
    assert b'Brad' in response.data  # Check if actor data is in the response

# Test for database error
@patch('main.get_db_connection')  # Mock the database connection
def test_actors_db_error(mock_db, client):
    # Mock the database cursor to raise an exception (simulate a database error)
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database error")
    
    # Simulate the GET request to /actors
    response = client.get('/actors')
    
    # Check if the response status code is 500 (internal server error)
    assert response.status_code == 500
    assert b"Error occurred while fetching actors" in response.data  # Check for the error message

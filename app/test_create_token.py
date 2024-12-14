import pytest
from unittest.mock import patch, MagicMock
from main import app  
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully retrieving tokens
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_tokens_success(mock_db, mock_authenticate, client):
    # Mock the authenticate function to simulate a successful user authentication
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate some tokens being returned for the user
    mock_cursor.fetchall.return_value = [('api_key_1',), ('api_key_2',)]  # Example tokens
    
    # Simulate the GET request to retrieve tokens
    response = client.get('/tokens')
    
    # Check if the response status code is 200 (success)
    assert response.status_code == 200
    assert b'tokens' in response.data
    assert b'api_key_1' in response.data
    assert b'api_key_2' in response.data

# Test for when no tokens are found
@patch('main.authenticate')  # Mock the authenticate function
@patch('main.get_db_connection')  # Mock the database connection
def test_get_tokens_no_tokens(mock_db, mock_authenticate, client):
    # Mock the authenticate function to simulate a successful user authentication
    mock_authenticate.return_value = {'success': True, 'user_id': 1}, 200

    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate no tokens found for the user
    mock_cursor.fetchall.return_value = []  # No tokens found
    
    # Simulate the GET request to retrieve tokens
    response = client.get('/tokens')
    
    # Check if the response status code is 404 (not found)
    assert response.status_code == 404
    assert b'No tokens found for this user' in response.data

# Test for failed authentication
@patch('main.authenticate')  # Mock the authenticate function
def test_get_tokens_authentication_failed(mock_authenticate, client):
    # Mock the authenticate function to simulate failed authentication
    mock_authenticate.return_value = {'success': False, 'message': 'Authentication failed'}, 401
    
    # Simulate the GET request to retrieve tokens
    response = client.get('/tokens')
    
    # Check if the response status code is 401 (unauthorized)
    assert response.status_code == 401
    assert b'Authentication failed' in response.data

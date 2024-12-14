import pytest
from unittest.mock import patch, MagicMock
from main import app
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successful signup followed by signin
@patch('main.get_db_connection')  # Mock the database connection
def test_signin_success(mock_db, client):
    # Mock the database cursor for signup
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no user found for the signup (this would be for the first time)
    mock_cursor.fetchone.return_value = None  # No user found for the signup
    mock_cursor.execute.return_value = None  # Simulate successful execution of insert query

    # Mock the cursor again for signin (it should return the user data)
    mock_cursor.fetchone.return_value = {
        'user_id': 1,
        'password': '$2b$12$l7lWkLH2sR9BnmZp.fDU2eSHl2zds4urS.psP6O0EeE904nzGK/tK', # bcrypt hash of 'password123'
        'is_admin': False
    }
    
    signin_response = client.post('/signin', json={
        'username': 'new_user',
        'password': 'password123'
    })
    
    # Check if the signin response status code is 200 (success)
    assert signin_response.status_code == 200
    assert b'Login successful' in signin_response.data
    assert b'user_id' in signin_response.data
    assert b'is_admin' in signin_response.data


# Test for invalid password
@patch('main.get_db_connection')  # Mock the database connection
def test_signin_invalid_password(mock_db, client):
    # Mock the database cursor for signin
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate the user record being returned from the database
    mock_cursor.fetchone.return_value = {
        'user_id': 1,
        'password': '$2b$12$G/DwYb2oIh6msNrDPSysW.qbbH5MhEjXYoE/VgllmIQN6Q.lOftoq',  # bcrypt hash of 'password123'
        'is_admin': False
    }
    
    # Send the POST request with an incorrect password
    response = client.post('/signin', json={
        'username': 'new_user',
        'password': 'wrongpassword'
    })
    
    # Check if the response status code is 401 (Unauthorized)
    assert response.status_code == 401
    assert b'Invalid password' in response.data

# Test for user not found
@patch('main.get_db_connection')  # Mock the database connection
def test_signin_user_not_found(mock_db, client):
    # Mock the database cursor for signin
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor

    # Simulate no user being found in the database (user does not exist)
    mock_cursor.fetchone.return_value = None
    
    # Send the POST request with a non-existent username
    response = client.post('/signin', json={
        'username': 'non_existent_user',
        'password': 'password123'
    })
    
    # Check if the response status code is 404 (Not Found)
    assert response.status_code == 404
    assert b'User not found' in response.data

# Test for missing credentials
def test_signin_missing_credentials(client):
    # Send the POST request with missing username
    response = client.post('/signin', json={'password': 'password123'})
    assert response.status_code == 400
    assert b'Username and password are required' in response.data

    # Send the POST request with missing password
    response = client.post('/signin', json={'username': 'test_user'})
    assert response.status_code == 400
    assert b'Username and password are required' in response.data

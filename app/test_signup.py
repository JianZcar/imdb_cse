import pytest
from flask import Flask, jsonify, request
from main import app 
from unittest.mock import patch

# You can use fixtures to set up reusable objects
@pytest.fixture
def client():
    app.config['TESTING'] = True  # Enable testing mode
    with app.test_client() as client:
        yield client  # Provide the test client for the test functions

@patch('main.get_db_connection')  # Mock the database connection
def test_signup_success(mock_db, client):
    # Mock the database cursor to simulate no existing user
    mock_cursor = mock_db.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = None  # Simulate that the user does not exist

    # Send the POST request
    response = client.post('/signup', json={
        'username': 'new_user',
        'password': 'password123'
    })

    # Check if the response status code is 201 (Created)
    assert response.status_code == 201
    assert b'User registered successfully' in response.data

# Example test: Test signup with an existing username
def test_signup_username_exists(client):
    response = client.post('/signup', json={
        'username': 'existing_user',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert b'Username already exists' in response.data

# Example test: Test signup with missing required fields
def test_signup_missing_fields(client):
    response = client.post('/signup', json={'username': 'new_user'})
    assert response.status_code == 400
    assert b'Username and password are required' in response.data

    response = client.post('/signup', json={'password': 'password123'})
    assert response.status_code == 400
    assert b'Username and password are required' in response.data

# Example test: Test internal error (e.g., DB error)
@patch('main.get_db_connection')  
def test_signup_internal_error(mock_db, client):
    mock_db.side_effect = Exception("Database connection failed")
    response = client.post('/signup', json={'username': 'new_user', 'password': 'password123'})
    assert response.status_code == 500
    assert b'An error occurred during signup' in response.data

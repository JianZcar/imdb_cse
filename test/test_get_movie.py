import pytest
from unittest.mock import patch, MagicMock
from main import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test for successfully retrieving movie details
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_by_id_success(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate the movie details being returned
    mock_cursor.fetchone.return_value = {
        'movie_id': 1,
        'movie_title': 'Inception',
        'release_year': 2010
    }

    # Simulate the reviews for the movie
    mock_cursor.execute.return_value = None  # Reset the cursor behavior between queries
    mock_cursor.fetchall.side_effect = [
        [{'star_rating': 5, 'review_text': 'Amazing movie!'}],  # Reviews
        [{'actor_id': 1, 'first_name': 'Leonardo', 'last_name': 'DiCaprio'}],  # Actors
        [{'movie_genres_type': 'Action'}, {'movie_genres_type': 'Sci-Fi'}]  # Genres
    ]
    
    # Simulate the GET request to retrieve the movie details
    response = client.get('/movies/1')
    
    # Check if the response status code is 200 (success)
    assert response.status_code == 200
    assert b'Inception' in response.data  # Movie title in the response
    assert b'Amazing movie!' in response.data  # Review text in the response
    assert b'Leonardo' in response.data  # Actor first name in the response
    assert b'DiCaprio' in response.data  # Actor last name in the response
    assert b'Sci-Fi' in response.data  # Genre in the response

# Test for when no movie is found by ID
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_by_id_not_found(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate no movie found for the given ID (None)
    mock_cursor.fetchone.return_value = None

    # Simulate the GET request to retrieve the movie details
    response = client.get('/movies/999')  # Assuming 999 does not exist
    
    # Check if the response status code is 404 (not found)
    assert response.status_code == 404
    assert b'Movie not found' in response.data  # Error message in the response


# Test for an internal server error
@patch('main.get_db_connection')  # Mock the database connection
def test_movie_by_id_internal_error(mock_db, client):
    # Mock the database cursor
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Simulate an error during the database query (e.g., database error)
    mock_cursor.fetchone.side_effect = Exception("Database error")

    # Simulate the GET request to retrieve the movie details
    response = client.get('/movies/1')
    
    # Check if the response status code is 500 (internal server error)
    assert response.status_code == 500
    assert b'Error occurred while fetching movie details' in response.data  # Error message in the response

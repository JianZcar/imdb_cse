from flask import Flask, render_template, request, jsonify
import pymysql
import bcrypt
import jwt
import os
import datetime
import time
from dotenv import load_dotenv

# Load .env
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

SECRET_KEY = os.getenv('SECRET_KEY')

session={}

app = Flask(__name__)

db_config = {
    'host': os.getenv('DB_HOST'), 
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    return pymysql.connect(**db_config)

# AUTH

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Check if the username already exists
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            connection.close()
            return jsonify({'error': 'Username already exists'}), 400

        # Hash the password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert the new user into the database
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password.decode('utf-8'))
        )
        connection.commit()
        connection.close()

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred during signup'}), 500


@app.route('/signin', methods=['POST'])
def signin():
    try:
        # Get the user input from the request
        username = request.json.get('username')
        password = request.json.get('password')

        # Validate that both username and password are provided
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the username exists
        cursor.execute("SELECT user_id, password, is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        connection.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify the password (compare the hashed password)
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid password'}), 401 
        session['user_id'] = user['user_id']
        session['hashed_password'] = user['password']
        session['is_admin'] = user['is_admin']
        # Return a success message
        return jsonify({'message': 'Login successful', 'user_id': user['user_id'], 'is_admin': user['is_admin']}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while signing in'}), 500

@app.route('/signout', methods=['POST'])
def signout():
    try:
        # Clear the session
        session.clear()
        return jsonify({'message': 'Successfully signed out'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while signing out'}), 500

@app.route('/tokens', methods=['GET'])
def get_tokens():
    try:
        # Authenticate the user using the `authenticate` function
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code
        user_id = auth_response['user_id']

        # Query the database for the user's API keys
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT api_key FROM user_keys WHERE user_id = %s", (user_id,))
        tokens = cursor.fetchall()
        connection.close()

        # Check if any tokens exist
        if not tokens:
            return jsonify({'message': 'No tokens found for this user'}), 404

        # Return the list of tokens (decoded)
        token_list = [token[0] for token in tokens]  # Assuming the token is stored in the first column
        return jsonify({'tokens': token_list}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while retrieving the tokens'}), 500

@app.route('/tokens', methods=['POST'])
def create_token():
    try:
        # Authenticate the user using the `authenticate` function
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code
        user_id = auth_response['user_id']

        # Get the requested expiration time from the POST request body
        data = request.get_json()
        expiration_hours = data.get('expiration_hours', 2)  # Default to 2 hours if not provided

        # Validate the expiration time
        if not isinstance(expiration_hours, (int, float)) or expiration_hours <= 0:
            return jsonify({'error': 'Invalid expiration time. Must be a positive number.'}), 400

        # Generate the JWT payload
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours)  # User-defined expiration
        }

        # Create the JWT using the application-wide SECRET_KEY
        api_key = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        hashed_api_key = bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt())

        # Store the JWT in the `user_keys` table
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO user_keys (user_id, api_key) VALUES (%s, %s)",
            (user_id, hashed_api_key.decode('utf-8'))
        )
        connection.commit()
        connection.close()

        # Return the token
        return jsonify({'message': 'JWT created successfully', 'api_key': api_key}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while creating the token'}), 500

@app.route('/tokens/<int:id>', methods=['DELETE'])
def delete_token(id):
    try:
        # Authenticate the user using the `authenticate` function
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code
        user_id = auth_response['user_id']

        # Query the database to check if the token exists for the user
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT api_key FROM user_keys WHERE user_id = %s AND id = %s", (user_id, id))
        token = cursor.fetchone()

        if not token:
            return jsonify({'message': 'Token not found for this user'}), 404

        # Delete the token from the database
        cursor.execute("DELETE FROM user_keys WHERE user_id = %s AND id = %s", (user_id, id))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Token deleted successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the token'}), 500

def authenticate(role=0, strict=False):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    user_id = session['user_id'] if 'user_id' in session else None
    hashed_password = session['hashed_password'] if 'hashed_password' in session else None
    key = request.headers.get('Authorization')
    try:
        if user_id and key:
            return {
                "message": "Conflicting authentication methods: Both user_id and API key provided.",
                "success": False
            }, 400
        # Case 1: Check for API key authentication
        if key:
            try:
                # Decode the JWT token and verify it
                decoded_token = jwt.decode(key, SECRET_KEY, algorithms=["HS256"])
                
                # Extract the user_id from the JWT payload
                user_id = decoded_token.get('user_id')
                
                # Check if the 'exp' field exists and if it's expired
                if decoded_token.get('exp') < int(time.time()):
                    return {"message": "API key has expired", "success": False}, 401

                # Find the JWT hash in the database associated with the user
                
                # Fetch all API keys for the user
                cursor.execute("SELECT api_key FROM user_keys WHERE user_id = %s", (user_id,))
                user_keys = cursor.fetchall()

                if not user_keys:
                    return {"message": "No stored API keys for this user", "success": False}, 401

                    # Check if the provided key matches any of the stored keys
                key_valid = any(bcrypt.checkpw(key.encode('utf-8'), stored_key['api_key'].encode('utf-8')) for stored_key in user_keys)

                if not key_valid:
                    print(f"Provided key: {key.encode('utf-8')}")
                    print(f"Stored keys: {[stored_key['api_key'] for stored_key in user_keys]}")
                    return {"message": "Invalid API key", "success": False}, 401

                # Proceed if the key is valid
                return {"message": "API key validated", "success": True, "user_id": user_id}, 200

            except jwt.ExpiredSignatureError:
                return {"message": "API key has expired", "success": False}, 401
            except jwt.InvalidTokenError:
                return {"message": "Invalid API key", "success": False}, 401
        
        # Case 2: Check for user authentication using user_id and password
        elif user_id and hashed_password:
            print(user_id)
            # Find user by user_id and check if password is correct
            cursor.execute("SELECT password, is_admin FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()

            if not user or not (user['password'] == hashed_password):
                return {"message": "Invalid credentials", "success": False}, 401                        
        else:
            # Handle missing session or token
            return {"message": "Authentication required. Please sign in or provide a valid API token.", "success": False}, 401

        # Case 3: Check if user has the required role
        cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return {"message": "User not found", "success": False}, 404
        
        # Ensure the user has the required role (0 for reviewer, 1 for admin)
        if role == 0 and user['is_admin'] != 0 and strict:
            return {"message": "Access denied, reviewer role required", "success": False}, 403
        elif role == 1 and user['is_admin'] != 1:
            return {"message": "Access denied, admin role required", "success": False}, 403
        
        # Authentication successful
        return {"message": "Authentication successful", "success": True, "user_id": user_id}, 200

    except Exception as e:
        print(f"Error: {e}")
        return {"message": "An error occurred during authentication", "success": False}, 500
    finally:
        connection.close()

@app.route('/movies', methods=['GET'])
def movies():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT movie_id, movie_title FROM movies")
        movies = cursor.fetchall()
        connection.close()

        # If no movies are found, return a 404 response
        if not movies:
            return jsonify({'error': 'No movies found'}), 404

        return jsonify({'movies': movies})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching movies", 500

@app.route('/movies/<int:id>', methods=['GET'])
def movie_by_id(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch the movie details
        cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()

        if movie:
            # Fetch reviews for the movie
            cursor.execute("SELECT star_rating, review_text FROM review WHERE movie_id = %s", (id,))
            reviews = cursor.fetchall()
            movie['reviews'] = reviews  # Add reviews to the movie details

            # Fetch actors for the movie
            cursor.execute("""
                SELECT a.actor_id, a.first_name, a.last_name
                FROM movie_actors ma
                JOIN actors a ON ma.actors_actor_id = a.actor_id
                WHERE ma.movies_movie_id = %s
            """, (id,))
            actors = cursor.fetchall()
            movie['actors'] = actors  # Add actors to the movie details

            # Fetch genres for the movie
            cursor.execute("""
                SELECT rg.movie_genres_type
                FROM movie_genres mg
                JOIN ref_movie_genres rg ON mg.ref_movie_genres_movie_genres_type = rg.movie_genres_type
                WHERE mg.movies_movie_id = %s
            """, (id,))
            genres = [genre['movie_genres_type'] for genre in cursor.fetchall()]
            movie['genres'] = genres  # Add genres to the movie details

            connection.close()
            return jsonify({'movie': movie})
        else:
            connection.close()
            return jsonify({'error': 'Movie not found'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching movie details", 500


@app.route('/movies', methods=['POST'])
def add_movie():
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code


        # Get the data from the request
        data = request.get_json()
        
        # Ensure the required fields are present
        if not data or 'title' not in data:
            return jsonify({'error': 'Missing required fields: title'}), 400

        # Insert the movie details into the 'movies' table
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO movies (movie_title)
            VALUES (%s)
        """, (data['title']))

        movie_id = cursor.lastrowid  # Get the id of the newly inserted movie
        connection.commit()

        # Commit the changes and close the connection
        connection.commit()
        connection.close()

        # Return the response with the new movie ID
        return jsonify({'message': 'Movie added successfully', 'movie_id': movie_id}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while adding the movie'}), 500

@app.route('/movies/<int:id>', methods=['PUT'])
def update_movie(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Get data from request
        data = request.json
        title = data.get('title')

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the movie exists
        cursor.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()

        if not movie:
            connection.close()
            return jsonify({'error': 'Movie not found'}), 404

        # Update movie details
        cursor.execute("UPDATE movies SET movie_title = %s WHERE movie_id = %s", (title, id))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Movie updated successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while updating the movie'}), 500


@app.route('/movies/<int:id>', methods=['DELETE'])
def delete_movie(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the movie exists
        cursor.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()

        if not movie:
            connection.close()
            return jsonify({'error': 'Movie not found'}), 404

        # Delete movie
        cursor.execute("DELETE FROM movies WHERE movie_id = %s", (id,))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Movie deleted successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the movie'}), 500

@app.route('/actors', methods=['GET'])
def actors():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch all actors
        cursor.execute("SELECT actor_id, first_name, last_name FROM actors")
        actors = cursor.fetchall()

        connection.close()
        return jsonify({'actors': actors})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching actors", 500


@app.route('/actors/<int:id>', methods=['GET'])
def actor_by_id(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch actor details
        cursor.execute("SELECT actor_id, first_name, last_name FROM actors WHERE actor_id = %s", (id,))
        actor = cursor.fetchone()

        if actor:
            # Fetch movies the actor has appeared in
            cursor.execute("""
                SELECT m.movie_id, m.movie_title
                FROM movie_actors ma
                JOIN movies m ON ma.movies_movie_id = m.movie_id
                WHERE ma.actors_actor_id = %s
            """, (id,))
            movies = cursor.fetchall()
            actor['movies'] = movies  # Add movies to the actor details

            connection.close()
            return jsonify({'actor': actor})
        else:
            connection.close()
            return jsonify({'error': 'Actor not found'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching actor details", 500

@app.route('/actors', methods=['POST'])
def create_actor():
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Get data from request
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not first_name or not last_name:
            return jsonify({'error': 'First name and last name are required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert new actor into the actors table
        cursor.execute("INSERT INTO actors (first_name, last_name) VALUES (%s, %s)", (first_name, last_name))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Actor created successfully'}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while creating the actor'}), 500

# Update actor route
@app.route('/actors/<int:id>', methods=['PUT'])
def update_actor(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Get data from request
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not first_name or not last_name:
            return jsonify({'error': 'First name and last name are required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the actor exists
        cursor.execute("SELECT actor_id FROM actors WHERE actor_id = %s", (id,))
        actor = cursor.fetchone()

        if not actor:
            connection.close()
            return jsonify({'error': 'Actor not found'}), 404

        # Update actor details
        cursor.execute("UPDATE actors SET first_name = %s, last_name = %s WHERE actor_id = %s", (first_name, last_name, id))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Actor updated successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while updating the actor'}), 500


@app.route('/actors/<int:id>', methods=['DELETE'])
def delete_actor(id):
    try:
        # Authenticate with role 1 (admin)
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the actor exists
        cursor.execute("SELECT actor_id FROM actors WHERE actor_id = %s", (id,))
        actor = cursor.fetchone()

        if not actor:
            connection.close()
            return jsonify({'error': 'Actor not found'}), 404

        # Delete the actor
        cursor.execute("DELETE FROM actors WHERE actor_id = %s", (id,))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Actor deleted successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the actor'}), 500

@app.route('/movies/<int:id>/reviews', methods=['GET'])
def get_reviews(id):
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch reviews for the specified movie
        cursor.execute("""
            SELECT review_id, star_rating, review_text 
            FROM review 
            WHERE movie_id = %s
        """, (id,))
        reviews = cursor.fetchall()
        connection.close()

        if not reviews:
            return jsonify({'message': 'No reviews found for this movie', 'success': False}), 404

        # Return the reviews
        return jsonify({'message': 'Reviews retrieved successfully', 'success': True, 'reviews': reviews}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching reviews', 'success': False}), 500

@app.route('/movies/<int:id>/reviews', methods=['POST'])
def add_review(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        user_id = auth_response['user_id']
        # Parse JSON payload
        data = request.get_json()

        # Validate required fields
        if not data or 'star_rating' not in data or 'review_text' not in data:
            return jsonify({"message": "Missing required fields: 'star_rating' and 'review_text'", "success": False}), 400

        # Extract and validate star_rating
        star_rating = data['star_rating']
        if not (0.0 <= star_rating <= 10.0):  # Assuming a 0-10 star rating scale
            return jsonify({"message": "Invalid 'star_rating'. It must be between 0.0 and 10.0", "success": False}), 400

        review_text = data['review_text']

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the movie exists
        cursor.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()
        if not movie:
            return jsonify({"message": f"Movie with ID {id} not found", "success": False}), 404

        # Insert the review
        cursor.execute(
            "INSERT INTO review (movie_id, user_id, star_rating, review_text) VALUES (%s, %s, %s, %s)",
            (id, user_id, star_rating, review_text)
        )
        connection.commit()

        return jsonify({"message": "Review added successfully", "success": True}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred while adding the review", "success": False}), 500

@app.route('/movies/<int:id>/genres', methods=['GET'])
def movie_genres(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch genres for the specified movie
        cursor.execute("""
            SELECT rg.movie_genres_type
            FROM movie_genres mg
            JOIN ref_movie_genres rg ON mg.ref_movie_genres_movie_genres_type = rg.movie_genres_type
            WHERE mg.movies_movie_id = %s
        """, (id,))
        genres = [genre['movie_genres_type'] for genre in cursor.fetchall()]
        
        connection.close()

        if genres:
            return jsonify({'genres': genres})
        else:
            return jsonify({'message': 'No genres found for this movie', 'success': False}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching genres', 'success': False}), 500


@app.route('/movies/<int:id>/genres', methods=['POST'])
def add_genre_to_movie(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code
        # Get the movie_genres_type from the request JSON
        data = request.json
        genre_type = data.get('movie_genres_type')

        # Validate the input
        if not genre_type:
            return jsonify({'error': 'Genre type is required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the movie exists
        cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()

        if not movie:
            return jsonify({'error': 'Movie not found'}), 404

        # Check if the genre exists in ref_movie_genres
        cursor.execute("SELECT * FROM ref_movie_genres WHERE movie_genres_type = %s", (genre_type,))
        genre = cursor.fetchone()

        if not genre:
            return jsonify({'error': 'Genre not found'}), 404

        # Check if the genre is already associated with the movie
        cursor.execute("""
            SELECT * FROM movie_genres WHERE movies_movie_id = %s AND ref_movie_genres_movie_genres_type = %s
        """, (id, genre_type))
        existing_association = cursor.fetchone()

        if existing_association:
            return jsonify({'message': 'Genre already associated with this movie'}), 200

        # Add the genre to the movie
        cursor.execute("""
            INSERT INTO movie_genres (movies_movie_id, ref_movie_genres_movie_genres_type)
            VALUES (%s, %s)
        """, (id, genre_type))

        # Commit the transaction
        connection.commit()

        # Now close the connection
        connection.close()
               
        return jsonify({'message': 'Genre added to the movie successfully'}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while adding genre to movie'}), 500


@app.route('/movies/<int:id>/actors', methods=['GET'])
def movie_actors(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch actors for the specified movie
        cursor.execute("""
            SELECT a.actor_id, a.first_name, a.last_name
            FROM movie_actors ma
            JOIN actors a ON ma.actors_actor_id = a.actor_id
            WHERE ma.movies_movie_id = %s
        """, (id,))
        actors = cursor.fetchall()
        
        connection.close()

        if actors:
            return jsonify({'actors': actors})
        else:
            return jsonify({'message': 'No actors found for this movie', 'success': False}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching actors', 'success': False}), 500


@app.route('/movies/<int:id>/actors', methods=['POST'])
def add_actor_to_movie(id):
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code
        # Get the actor_id from the request JSON
        data = request.json
        actor_id = data.get('actor_id')

        # Validate the input
        if not actor_id:
            return jsonify({'error': 'Actor ID is required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the movie exists
        cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (id,))
        movie = cursor.fetchone()
        
        if not movie:
            connection.close()
            return jsonify({'error': 'Movie not found'}), 404

        # Check if the actor exists
        cursor.execute("SELECT * FROM actors WHERE actor_id = %s", (actor_id,))
        actor = cursor.fetchone()
        
        if not actor:
            connection.close()
            return jsonify({'error': 'Actor not found'}), 404

        # Check if the actor is already associated with the movie
        cursor.execute("""
            SELECT * FROM movie_actors WHERE movies_movie_id = %s AND actors_actor_id = %s
        """, (id, actor_id))
        existing_association = cursor.fetchone()

        if existing_association:
            connection.close()
            return jsonify({'message': 'Actor already associated with this movie'}), 200

        # Add the actor to the movie
        cursor.execute("""
            INSERT INTO movie_actors (movies_movie_id, actors_actor_id)
            VALUES (%s, %s)
        """, (id, actor_id))

        # Commit the transaction
        connection.commit()
        connection.close()

        return jsonify({'message': 'Actor added to the movie successfully'}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while adding actor to movie'}), 500

@app.route('/genres')
def genres():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch all genres
        cursor.execute("SELECT movie_genres_type FROM ref_movie_genres")
        genres = [row['movie_genres_type'] for row in cursor.fetchall()]

        connection.close()
        return jsonify({'genres': genres})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error occurred while fetching genres'}), 500

@app.route('/genres', methods=['POST'])
def add_genre():
    try:
        auth_response, status_code = authenticate(role=1)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Get the new genre data from the request
        new_genre = request.json.get('movie_genres_type')

        if not new_genre:
            return jsonify({'error': 'Genre type is required'}), 400

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the genre already exists
        cursor.execute("SELECT movie_genres_type FROM ref_movie_genres WHERE movie_genres_type = %s", (new_genre,))
        existing_genre = cursor.fetchone()

        if existing_genre:
            connection.close()
            return jsonify({'error': 'Genre already exists'}), 400

        # Insert the new genre into the database
        cursor.execute("INSERT INTO ref_movie_genres (movie_genres_type) VALUES (%s)", (new_genre,))
        connection.commit()

        connection.close()
        return jsonify({'message': 'Genre added successfully'}), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error occurred while adding the genre'}), 500

@app.route('/genres/<string:genre>')
def genre_by_type(genre):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the genre exists
        cursor.execute("SELECT movie_genres_type FROM ref_movie_genres WHERE movie_genres_type = %s", (genre,))
        genre_data = cursor.fetchone()

        if genre_data:
            # Fetch movies associated with the genre
            cursor.execute("""
                SELECT m.movie_id, m.movie_title
                FROM movie_genres mg
                JOIN movies m ON mg.movies_movie_id = m.movie_id
                WHERE mg.ref_movie_genres_movie_genres_type = %s
            """, (genre,))
            movies = cursor.fetchall()
            genre_data['movies'] = movies  # Add movies to the genre details

            connection.close()
            return jsonify({'genre': genre_data})
        else:
            connection.close()
            return jsonify({'error': 'Genre not found'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching genre details", 500


@app.route('/genres/<string:genre>', methods=['DELETE'])
def delete_genre(genre):
    try:
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the genre exists in the ref_movie_genres table
        cursor.execute("SELECT movie_genres_type FROM ref_movie_genres WHERE movie_genres_type = %s", (genre,))
        genre_data = cursor.fetchone()

        if not genre_data:
            connection.close()
            return jsonify({'error': 'Genre not found'}), 404

        # Delete all associated movie-genre relationships
        cursor.execute("DELETE FROM movie_genres WHERE ref_movie_genres_movie_genres_type = %s", (genre,))
        
        # Now delete the genre from the ref_movie_genres table
        cursor.execute("DELETE FROM ref_movie_genres WHERE movie_genres_type = %s", (genre,))
        
        connection.commit()
        connection.close()

        return jsonify({'message': 'Genre deleted successfully', 'success': True}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching the genre', 'success': False}), 500


@app.route('/profile/reviews', methods=['GET'])
def get_user_reviews():
    try:
        # Authenticate the user
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        user_id = auth_response['user_id']

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch reviews created by the authenticated user
        cursor.execute("""
            SELECT r.review_id, r.movie_id, r.star_rating, r.review_text, m.movie_title
            FROM review r
            JOIN movies m ON r.movie_id = m.movie_id
            WHERE r.user_id = %s
        """, (user_id,))
        reviews = cursor.fetchall()
        
        connection.close()

        if reviews:
            return jsonify({'reviews': reviews})
        else:
            return jsonify({'message': 'No reviews found for this user', 'success': False}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching reviews', 'success': False}), 500


@app.route('/profile/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        # Authenticate the user
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        user_id = auth_response['user_id']

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the review exists and if the authenticated user created it
        cursor.execute("""
            SELECT user_id FROM review WHERE review_id = %s
        """, (review_id,))
        review = cursor.fetchone()

        if not review:
            connection.close()
            return jsonify({'error': 'Review not found'}), 404
        
        if review['user_id'] != user_id:
            connection.close()
            return jsonify({'error': 'You can only delete your own reviews'}), 403

        # Delete the review
        cursor.execute("""
            DELETE FROM review WHERE review_id = %s
        """, (review_id,))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Review deleted successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the review'}), 500


@app.route('/profile/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    try:
        # Authenticate the user
        auth_response, status_code = authenticate(role=0)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        user_id = auth_response['user_id']

        # Get the updated data from the request
        data = request.json
        star_rating = data.get('star_rating')
        review_text = data.get('review_text')

        if not star_rating or not review_text:
            return jsonify({'error': 'Star rating and review text are required'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Check if the review exists and if the authenticated user created it
        cursor.execute("""
            SELECT user_id FROM review WHERE review_id = %s
        """, (review_id,))
        review = cursor.fetchone()

        if not review:
            connection.close()
            return jsonify({'error': 'Review not found'}), 404
        
        if review['user_id'] != user_id:
            connection.close()
            return jsonify({'error': 'You can only update your own reviews'}), 403

        # Update the review
        cursor.execute("""
            UPDATE review
            SET star_rating = %s, review_text = %s
            WHERE review_id = %s
        """, (star_rating, review_text, review_id))
        connection.commit()
        connection.close()

        return jsonify({'message': 'Review updated successfully'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while updating the review'}), 500


@app.route('/reviews', methods=['GET'])
def get_all_reviews():
    try:
        # Authenticate the user (Admin role=1)
        auth_response, status_code = authenticate(role=1)  # Admin role is 1
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch all reviews from the database
        cursor.execute("""
            SELECT r.review_id, r.movie_id, r.star_rating, r.review_text, m.movie_title, u.username
            FROM review r
            JOIN movies m ON r.movie_id = m.movie_id
            JOIN users u ON r.user_id = u.user_id
        """)
        reviews = cursor.fetchall()
        
        connection.close()

        if reviews:
            return jsonify({'reviews': reviews})
        else:
            return jsonify({'message': 'No reviews found', 'success': False}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching reviews', 'success': False}), 500


@app.route('/reviews/<int:review_id>', methods=['GET'])
def get_specific_review(review_id):
    try:
        # Authenticate the user (Admin role=1)
        auth_response, status_code = authenticate(role=1)  # Admin role is 1
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch the specific review from the database
        cursor.execute("""
            SELECT r.review_id, r.movie_id, r.star_rating, r.review_text, m.movie_title, u.username
            FROM review r
            JOIN movies m ON r.movie_id = m.movie_id
            JOIN users u ON r.user_id = u.user_id
            WHERE r.review_id = %s
        """, (review_id,))
        review = cursor.fetchone()
        
        connection.close()

        if review:
            return jsonify({'review': review})
        else:
            return jsonify({'message': 'Review not found', 'success': False}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching the review', 'success': False}), 500


@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_specific_review(review_id):
    try:
        # Authenticate the user (Admin role=1)
        auth_response, status_code = authenticate(role=1)  # Admin role is 1
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the review exists
        cursor.execute("SELECT review_id FROM review WHERE review_id = %s", (review_id,))
        review = cursor.fetchone()

        if not review:
            connection.close()
            return jsonify({'message': 'Review not found', 'success': False}), 404

        # Delete the review from the database
        cursor.execute("DELETE FROM review WHERE review_id = %s", (review_id,))
        connection.commit()

        connection.close()

        return jsonify({'message': 'Review deleted successfully', 'success': True}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the review', 'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

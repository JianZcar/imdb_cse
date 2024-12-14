from flask import Flask, render_template, request, jsonify
import pymysql
import bcrypt
import jwt
import os
import datetime
import time
from dotenv import load_dotenv

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construct the path to the .env file
dotenv_path = os.path.join(root_dir, ".env")

# Load the .env file from the root directory
load_dotenv(dotenv_path)

SECRET_KEY = os.getenv('SECRET_KEY')

session={}

app = Flask(__name__)

db_config = {
    'host': os.getenv('DB_HOST'), #The ip address of the container
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
        session['userid'] = user['user_id']
        session['hashed_password'] = user['password']
        session['is_admin'] = user['is_admin']
        # Return a success message
        return jsonify({'message': 'Login successful', 'user_id': user['user_id'], 'is_admin': user['is_admin']}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while signing in'}), 500

@app.route('/create_token', methods=['POST'])
def create_token():
    try:
        # Check if the user is signed in
        if 'userid' not in session or 'hashed_password' not in session:
            return jsonify({'error': 'User is not signed in'}), 401

        # Get user details from session
        user_id = session['userid']
        hashed_password = session['hashed_password']

        # Authenticate the user using the `authenticate` function
        auth_response, status_code = authenticate(user_id=user_id, hashed_password=hashed_password)
        if not auth_response['success']:
            return jsonify(auth_response), status_code

        # Get the requested expiration time from the POST request body
        data = request.get_json()
        expiration_hours = data.get('expiration_hours', 2)  # Default to 2 hours if not provided

        # Validate the expiration time
        if not isinstance(expiration_hours, (int, float)) or expiration_hours <= 0:
            return jsonify({'error': 'Invalid expiration time. Must be a positive number.'}), 400

        # Generate the JWT payload
        payload = {
            'user_id': user_id,
            'role': 'admin' if auth_response.get('is_admin') else 'reviewer',
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

def authenticate(role=0, key=None, user_id=None, hashed_password=None, strict=False):
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
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
                cursor.execute("SELECT api_key FROM user_keys WHERE user_id = %s", (user_id,))
                user_key = cursor.fetchone()

                if not user_key:
                    return {"message": "No stored API key for this user", "success": False}, 401
                
                # Hash the JWT key and compare with the stored hash
                if not bcrypt.checkpw(key.encode('utf-8'), user_key['api_key'].encode('utf-8')):
                    return {"message": "Invalid API key", "success": False}, 401

            except jwt.ExpiredSignatureError:
                return {"message": "API key has expired", "success": False}, 401
            except jwt.InvalidTokenError:
                return {"message": "Invalid API key", "success": False}, 401
        
        # Case 2: Check for user authentication using user_id and password
        if user_id and hashed_password:
            # Find user by user_id and check if password is correct
            cursor.execute("SELECT password, is_admin FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()

            if not user or not (user['password'] == hashed_password):
                return {"message": "Invalid credentials", "success": False}, 401                        

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

@app.route('/movies')
def movies():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT movie_id, movie_title FROM movies")
        movies = cursor.fetchall()
        connection.close()
        return jsonify({'movies': movies})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching movies", 500

@app.route('/movies/<int:id>')
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

@app.route('/actors')
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


@app.route('/actors/<int:id>')
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

@app.route('/genres')
def genres():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Fetch all genres
        cursor.execute("SELECT movie_genres_type FROM ref_movie_genres")
        genres = cursor.fetchall()

        connection.close()
        return jsonify({'genres': genres})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching genres", 500

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



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

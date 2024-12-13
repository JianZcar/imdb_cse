from flask import Flask, render_template, request, jsonify
import pymysql

app = Flask(__name__)

db_config = {
    'host': '10.89.0.2', #The ip address of the container
    'user': 'root',
    'password': '',
    'database': 'imdb'
}

def get_db_connection():
    return pymysql.connect(**db_config)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

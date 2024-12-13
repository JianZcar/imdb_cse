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

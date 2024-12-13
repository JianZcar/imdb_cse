from flask import Flask, render_template, request
import pymysql
import json

# Initialize Flask app
app = Flask(__name__)

# Database connection details
db_config = {
    'host': '10.89.0.2',
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
        return json.dumps({'movies': movies})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred while fetching movies", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

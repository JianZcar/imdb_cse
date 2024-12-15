# IMDB CSE

## Description
IMDB CSE is a web application built with Flask that provides various functionalities for managing and retrieving information related to movies, users, and reviews. The application uses a MySQL database for data storage and JWT for authentication.

## Features
- User Authentication: Signup, Signin, Signout
- JWT Token Management: Create, retrieve and delete API tokens
- Movie Management: Add, update, delete, and retrieve movies
- Review Management: Add, update, delete, and retrieve reviews
- Actor Management: Add, update, delete, and retrieve actors
- Genre Management: Add, delete, and retrieve genres
- API Endpoints for managing relationships between movies, actors, and genres

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/JianZcar/imdb_cse.git
    ```
2. Navigate to the project directory:
    ```sh
    cd imdb_cse
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Set up the environment variables by creating a `.env` file in the root directory with the following variables:
    ```
    SECRET_KEY=<your_secret_key>
    DB_HOST=<your_db_host>
    DB_USER=<your_db_user>
    DB_PASSWORD=<your_db_password>
    DB_NAME=<your_db_name>
    ```

## Usage
1. Start the Flask application:
    ```sh
    flask run
    ```
2. Access the application at `http://127.0.0.1:5000`.

## API Endpoints
- **User Authentication**
  - `POST /signup`: Register a new user
  - `POST /signin`: Sign in an existing user
  - `POST /signout`: Sign out the current user

- **JWT Token Management**
  - `GET /tokens`: Retrieve API tokens for the current user
  - `POST /tokens`: Create a new API token
  - `DELETE /tokens/<int:id>`: Delete a specific API token

- **Movie Management**
  - `GET /movies`: Retrieve all movies
  - `GET /movies/<int:id>`: Retrieve a specific movie by ID
  - `POST /movies`: Add a new movie
  - `PUT /movies/<int:id>`: Update a specific movie by ID
  - `DELETE /movies/<int:id>`: Delete a specific movie by ID

- **Review Management**
  - `GET /movies/<int:id>/reviews`: Retrieve reviews for a specific movie
  - `POST /movies/<int:id>/reviews`: Add a review for a specific movie

- **Actor Management**
  - `GET /actors`: Retrieve all actors
  - `GET /actors/<int:id>`: Retrieve a specific actor by ID
  - `POST /actors`: Add a new actor
  - `PUT /actors/<int:id>`: Update a specific actor by ID
  - `DELETE /actors/<int:id>`: Delete a specific actor by ID

- **Genre Management**
  - `GET /genres`: Retrieve all genres
  - `GET /genres/<string:genre>`: Retrieve movies associated with a specific genre
  - `POST /genres`: Add a new genre
  - `DELETE /genres/<string:genre>`: Delete a specific genre

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## License
This project is licensed under the MIT License.

## Contact
For any inquiries, please contact [JianZcar](https://github.com/JianZcar).

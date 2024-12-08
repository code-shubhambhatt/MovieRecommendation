import pandas as pd
from flask import Flask, render_template, request
import traceback

app = Flask(__name__)

# Load datasets
ratings_path = 'data/file.tsv'  # Path to the ratings file
titles_path = 'data/Movie_Id_Titles.csv'  # Path to the titles file

# Read ratings data
ratings_columns = ['user_id', 'item_id', 'rating', 'timestamp']
ratings = pd.read_csv(ratings_path, sep='\t', names=ratings_columns)

# Read movie titles data
titles = pd.read_csv(titles_path)

# Merge ratings with titles
data = pd.merge(ratings, titles, on='item_id')

# Create a pivot table
moviemat = data.pivot_table(index='user_id', columns='title', values='rating')

# Calculate average ratings and number of ratings per movie
movie_ratings = pd.DataFrame(data.groupby('title')['rating'].mean())
movie_ratings['num_of_ratings'] = data.groupby('title')['rating'].count()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        # Get the movie title input by the user
        movie_title = request.form['movie_title'].strip().lower()
        print(f"User input (normalized): {movie_title}")  # Debug: Print normalized input

        # Normalize the column names in the pivot table
        normalized_titles = moviemat.columns.str.strip().str.lower()
        print(f"Available movie titles (normalized): {list(normalized_titles)}")  # Debug: Print all normalized titles

        # Perform partial matching
        matching_titles = [title for title in moviemat.columns if movie_title in title.lower()]
        print(f"Matching titles: {matching_titles}")  # Debug: Print matching titles

        # If no matches are found, show an error
        if not matching_titles:
            return render_template(
                'index.html',
                error=f'Movie "{movie_title}" not found in the database. Please try another movie.'
            )

        # If multiple matches are found, take the first one
        exact_title = matching_titles[0]
        print(f"Exact title matched: {exact_title}")  # Debug: Print exact title matched

        # Get recommendations based on the matched movie
        user_ratings = moviemat[exact_title]
        similar_movies = moviemat.corrwith(user_ratings)

        corr_movies = pd.DataFrame(similar_movies, columns=['Correlation'])
        corr_movies.dropna(inplace=True)

        corr_movies = corr_movies.join(movie_ratings['num_of_ratings'])
        recommendations = corr_movies[corr_movies['num_of_ratings'] > 100].sort_values(
            'Correlation', ascending=False).head(10)

        return render_template('index.html', recommendations=list(recommendations.index))
    except Exception as e:
        print(f"Error: {e}")  # Debug: Print the error
        print(f"Traceback: {traceback.format_exc()}")  # Print the full error traceback for debugging
        return render_template(
            'index.html',
            error="An unexpected error occurred. Please try again."
        )


if __name__ == '__main__':
    app.run(debug=True)

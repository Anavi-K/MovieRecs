import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------------
# 1. Load the movie dataset
# -----------------------------------

movies = pd.read_csv("../data/movies.csv")

print("Number of movies:", len(movies))


# -----------------------------------
# 2. Convert genres into numbers
# -----------------------------------

tfidf = TfidfVectorizer(token_pattern=r"[^|]+")

tfidf_matrix = tfidf.fit_transform(movies["genres"])

print("TF-IDF matrix shape:", tfidf_matrix.shape)


# -----------------------------------
# 3. Calculate movie similarity
# -----------------------------------

similarity_matrix = cosine_similarity(tfidf_matrix)

print("Similarity matrix shape:", similarity_matrix.shape)


# -----------------------------------
# 4. Recommendation function
# -----------------------------------

def recommend_movies(movie_title, num_recommendations=5):

    # Find movies matching the user's search
    matches = movies[
        movies["title"].str.contains(
            movie_title,
            case=False,
            na=False
        )
    ]

    # If no movie was found
    if len(matches) == 0:
        return "Movie not found"

    # Use the first matching movie
    movie_index = matches.index[0]

    # Get similarity scores for that movie
    similarity_scores = similarity_matrix[movie_index]

    # Sort movies by similarity
    similar_movies = sorted(
        enumerate(similarity_scores),
        key=lambda x: x[1],
        reverse=True
    )

    # Store recommendations
    recommendations = []

    # Skip the movie itself
    for index, score in similar_movies[1:num_recommendations + 1]:

        recommendations.append({
            "movieId": int(movies.iloc[index]["movieId"]),
            "title": movies.iloc[index]["title"],
            "similarity": round(float(score), 3)
        })

    return recommendations
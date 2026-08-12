import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------------
# 1. Load datasets
# -----------------------------------

ratings = pd.read_csv("../data/ratings.csv")
movies = pd.read_csv("../data/movies.csv")

print("Ratings loaded:", len(ratings))
print("Movies loaded:", len(movies))


# -----------------------------------
# 2. Create user-movie matrix
# -----------------------------------

user_movie_matrix = ratings.pivot_table(
    index="userId",
    columns="movieId",
    values="rating"
)

print("User-movie matrix shape:", user_movie_matrix.shape)


# -----------------------------------
# 3. Replace missing ratings with 0
# -----------------------------------

user_movie_matrix = user_movie_matrix.fillna(0)


# -----------------------------------
# 4. Calculate movie similarity
# -----------------------------------

movie_similarity = cosine_similarity(
    user_movie_matrix.T
)

print(
    "Movie similarity matrix shape:",
    movie_similarity.shape
)


# -----------------------------------
# 5. Recommendation function
# -----------------------------------

def recommend_collaborative(movie_id, num_recommendations=5):

    # Check if movie exists
    if movie_id not in user_movie_matrix.columns:
        return "Movie not found"

    # Find movie position
    movie_index = user_movie_matrix.columns.get_loc(movie_id)

    # Get similarity scores
    similarity_scores = movie_similarity[movie_index]

    # Sort by similarity
    similar_movies = sorted(
        enumerate(similarity_scores),
        key=lambda x: x[1],
        reverse=True
    )

    recommendations = []

    # Skip the movie itself
    for index, score in similar_movies[1:num_recommendations + 1]:

        recommended_movie_id = int(
            user_movie_matrix.columns[index]
        )

        # Find movie information
        movie_info = movies[
            movies["movieId"] == recommended_movie_id
        ]

        if len(movie_info) > 0:

            recommendations.append({
                "movieId": recommended_movie_id,
                "title": movie_info.iloc[0]["title"],
                "similarity": round(float(score), 3)
            })

    return recommendations


# -----------------------------------
# 6. Test with Toy Story
# -----------------------------------

print()
print("Collaborative recommendations:")

recommendations = recommend_collaborative(1)

for movie in recommendations:
    print(movie)
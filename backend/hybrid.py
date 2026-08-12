import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ===================================
# 1. Load datasets
# ===================================

movies = pd.read_csv("../data/movies.csv")
ratings = pd.read_csv("../data/ratings.csv")

print("Movies:", len(movies))
print("Ratings:", len(ratings))


# ===================================
# 2. Content-based model
# ===================================

tfidf = TfidfVectorizer(token_pattern=r"[^|]+")

tfidf_matrix = tfidf.fit_transform(movies["genres"])

content_similarity = cosine_similarity(tfidf_matrix)

print(
    "Content similarity matrix:",
    content_similarity.shape
)


# ===================================
# 3. Collaborative model
# ===================================

user_movie_matrix = ratings.pivot_table(
    index="userId",
    columns="movieId",
    values="rating"
)

user_movie_matrix = user_movie_matrix.fillna(0)

collaborative_similarity = cosine_similarity(
    user_movie_matrix.T
)

print(
    "Collaborative similarity matrix:",
    collaborative_similarity.shape
)


# ===================================
# 4. Hybrid recommendation function
# ===================================

def recommend_hybrid(movie_title, num_recommendations=5):

    # Find the movie
    matches = movies[
        movies["title"].str.contains(
            movie_title,
            case=False,
            na=False
        )
    ]

    if len(matches) == 0:
        return "Movie not found"

    # Use the first matching movie
    movie_index = matches.index[0]

    movie_id = int(
        movies.iloc[movie_index]["movieId"]
    )

    # -----------------------------------
    # Content-based scores
    # -----------------------------------

    content_scores = content_similarity[movie_index]

    # -----------------------------------
    # Collaborative scores
    # -----------------------------------

    if movie_id in user_movie_matrix.columns:

        collaborative_index = (
            user_movie_matrix.columns.get_loc(movie_id)
        )

        collaborative_scores = (
            collaborative_similarity[
                collaborative_index
            ]
        )

        collaborative_score_map = dict(
            zip(
                user_movie_matrix.columns,
                collaborative_scores
            )
        )

    else:
        collaborative_score_map = {}

    # -----------------------------------
    # Combine scores
    # -----------------------------------

    hybrid_scores = []

    for index, row in movies.iterrows():

        recommended_movie_id = int(row["movieId"])

        content_score = content_scores[index]

        collaborative_score = collaborative_score_map.get(
            recommended_movie_id,
            0
        )

        # 40% content + 60% collaborative
        hybrid_score = (
            0.4 * content_score
            + 0.6 * collaborative_score
        )

        hybrid_scores.append(
            (index, hybrid_score)
        )

    # -----------------------------------
    # Sort recommendations
    # -----------------------------------

    hybrid_scores.sort(
        key=lambda x: x[1],
        reverse=True
    )

    recommendations = []

    for index, score in hybrid_scores:

        # Don't recommend the movie itself
        if index == movie_index:
            continue

        recommendations.append({
            "movieId": int(
                movies.iloc[index]["movieId"]
            ),
            "title": movies.iloc[index]["title"],
            "score": round(float(score), 3)
        })

        if len(recommendations) == num_recommendations:
            break

    return recommendations
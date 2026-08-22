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

tfidf_matrix = tfidf.fit_transform(
    movies["genres"].fillna("")
)

print(
    "TF-IDF matrix:",
    tfidf_matrix.shape
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

print(
    "User-movie matrix:",
    user_movie_matrix.shape
)


# ===================================
# 4. Hybrid recommendation function
# ===================================

def recommend_hybrid(movie_title, num_recommendations=5):

    # -----------------------------------
    # Find the movie
    # -----------------------------------

    matches = movies[
        movies["title"].str.contains(
            movie_title,
            case=False,
            na=False,
            regex=False
        )
    ]

    if len(matches) == 0:
        return "Movie not found"

    # Use the first matching movie
    movie_index = matches.index[0]

    movie_id = int(
        movies.iloc[movie_index]["movieId"]
    )

    print(
        f"Recommendation movie: "
        f"{movies.iloc[movie_index]['title']}"
    )

    # -----------------------------------
    # Content-based scores
    # -----------------------------------

    # Calculate similarity ONLY for this movie
    content_scores = cosine_similarity(
        tfidf_matrix[movie_index],
        tfidf_matrix
    ).flatten()

    # -----------------------------------
    # Collaborative scores
    # -----------------------------------

    collaborative_score_map = {}

    if movie_id in user_movie_matrix.columns:

        collaborative_index = (
            user_movie_matrix.columns.get_loc(
                movie_id
            )
        )

        # Calculate similarity ONLY for this movie
        collaborative_scores = cosine_similarity(
            user_movie_matrix.T.iloc[
                [collaborative_index]
            ],
            user_movie_matrix.T
        ).flatten()

        collaborative_score_map = dict(
            zip(
                user_movie_matrix.columns,
                collaborative_scores
            )
        )

    # -----------------------------------
    # Combine scores
    # -----------------------------------

    hybrid_scores = []

    for index, row in movies.iterrows():

        # Don't recommend the movie itself
        if index == movie_index:
            continue

        recommended_movie_id = int(
            row["movieId"]
        )

        content_score = float(
            content_scores[index]
        )

        collaborative_score = float(
            collaborative_score_map.get(
                recommended_movie_id,
                0
            )
        )

        # 40% content + 60% collaborative
        hybrid_score = (
            0.4 * content_score
            + 0.6 * collaborative_score
        )

        hybrid_scores.append(
            (
                index,
                hybrid_score
            )
        )

    # -----------------------------------
    # Sort recommendations
    # -----------------------------------

    hybrid_scores.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # -----------------------------------
    # Build result
    # -----------------------------------

    recommendations = []

    for index, score in hybrid_scores:

        recommendations.append({
            "movieId": int(
                movies.iloc[index]["movieId"]
            ),
            "title": movies.iloc[index]["title"],
            "score": round(
                float(score),
                3
            )
        })

        if len(recommendations) >= num_recommendations:
            break

    return recommendations


# ===================================
# 5. Personalized recommendation for user (from watched history)
# ===================================

def recommend_personalized(watched_movie_ids, num_recommendations=10):
    if not watched_movie_ids:
        return []

    watched_set = set(int(mid) for mid in watched_movie_ids)
    total_movies = len(movies)

    accumulated_scores = [0.0] * total_movies
    count_valid_watched = 0

    for watched_id in watched_movie_ids:
        matches = movies[movies["movieId"] == watched_id]
        if len(matches) == 0:
            continue

        movie_index = matches.index[0]
        count_valid_watched += 1

        # Content scores
        content_scores = cosine_similarity(
            tfidf_matrix[movie_index],
            tfidf_matrix
        ).flatten()

        # Collaborative scores
        collaborative_score_map = {}
        if watched_id in user_movie_matrix.columns:
            collab_index = user_movie_matrix.columns.get_loc(watched_id)
            collaborative_scores = cosine_similarity(
                user_movie_matrix.T.iloc[[collab_index]],
                user_movie_matrix.T
            ).flatten()
            collaborative_score_map = dict(
                zip(user_movie_matrix.columns, collaborative_scores)
            )

        for idx, row in movies.iterrows():
            mid = int(row["movieId"])
            if mid in watched_set:
                continue

            c_score = float(content_scores[idx])
            collab_score = float(collaborative_score_map.get(mid, 0))
            h_score = 0.4 * c_score + 0.6 * collab_score
            accumulated_scores[idx] += h_score

    if count_valid_watched == 0:
        return []

    candidate_scores = []
    for idx, row in movies.iterrows():
        mid = int(row["movieId"])
        if mid in watched_set:
            continue
        avg_score = accumulated_scores[idx] / count_valid_watched
        candidate_scores.append((idx, avg_score))

    candidate_scores.sort(key=lambda x: x[1], reverse=True)

    recommendations = []
    for idx, score in candidate_scores[:num_recommendations]:
        recommendations.append({
            "movieId": int(movies.iloc[idx]["movieId"]),
            "title": movies.iloc[idx]["title"],
            "score": round(float(score), 3)
        })

    return recommendations
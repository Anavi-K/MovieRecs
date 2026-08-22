import os
import re
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import pandas as pd
import requests

from database import db, User, Watchlist, Watched
from hybrid import recommend_hybrid, recommend_personalized

load_dotenv()


# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "movie-recommendation-secret-key"

# Use the SAME database everywhere
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie_recs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Local frontend + backend sessions
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

db.init_app(app)

bcrypt = Bcrypt(app)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
)


# =========================================================
# TMDB & DATA MAPPINGS
# =========================================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

MOVIE_TO_TMDB_MAP = {}
MOVIE_TO_GENRES_MAP = {}
TITLE_TO_MOVIE_ID_MAP = {}

try:
    links_df = pd.read_csv(os.path.join(DATA_DIR, "links.csv")).dropna(subset=["tmdbId"])
    MOVIE_TO_TMDB_MAP = dict(zip(links_df["movieId"].astype(int), links_df["tmdbId"].astype(int)))
except Exception as e:
    print("Could not load links.csv:", e)

try:
    movies_df = pd.read_csv(os.path.join(DATA_DIR, "movies.csv"))
    MOVIE_TO_GENRES_MAP = dict(zip(movies_df["movieId"].astype(int), movies_df["genres"]))
    TITLE_TO_MOVIE_ID_MAP = dict(zip(movies_df["title"], movies_df["movieId"].astype(int)))
except Exception as e:
    print("Could not load movies.csv:", e)

TMDB_CACHE = {}


# =========================================================
# DATABASE
# =========================================================

with app.app_context():
    db.create_all()


# =========================================================
# TMDB HELPER
# =========================================================

def clean_movie_title(title):
    year_match = re.search(r"\((\d{4})\)\s*$", title)
    year = year_match.group(1) if year_match else None

    clean = re.sub(r"\(.*?\)", "", title).strip()

    articles = ["The", "A", "An", "La", "Le", "Les", "El", "Il", "Der", "Die", "Das"]
    for art in articles:
        if clean.endswith(f", {art}"):
            clean = f"{art} " + clean[:-len(f", {art}")]
            break

    return clean.strip(), year


def fetch_wikipedia_poster_and_overview(clean_title, year=None):
    headers = {"User-Agent": "MovieRecApp/1.0 (contact@movierec.local)"}
    query = f"{clean_title} {year} film" if year else f"{clean_title} film"

    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json"
        resp = requests.get(search_url, headers=headers, timeout=4)
        if resp.status_code != 200:
            return None

        search_results = resp.json().get("query", {}).get("search", [])
        if not search_results:
            return None

        page_title = search_results[0]["title"]

        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(page_title)}"
        summary_resp = requests.get(summary_url, headers=headers, timeout=4)
        if summary_resp.status_code == 200:
            data = summary_resp.json()
            thumb = data.get("thumbnail", {}).get("source")
            extract = data.get("extract")
            return {"poster": thumb, "overview": extract}
    except Exception as err:
        print(f"Wikipedia fetch error for '{clean_title}': {err}")

    return None


def get_tmdb_movie(title, movie_id=None):
    if not movie_id and title in TITLE_TO_MOVIE_ID_MAP:
        movie_id = TITLE_TO_MOVIE_ID_MAP[title]

    cache_key = (movie_id, title)
    if cache_key in TMDB_CACHE:
        return TMDB_CACHE[cache_key]

    cleaned_title, extracted_year = clean_movie_title(title)
    raw_genres = MOVIE_TO_GENRES_MAP.get(movie_id, "")
    formatted_genres = (
        raw_genres.replace("|", ", ")
        if raw_genres and raw_genres != "(no genres listed)"
        else ""
    )

    fallback_overview = f"'{cleaned_title}'"
    if extracted_year:
        fallback_overview += f" ({extracted_year})"
    if formatted_genres:
        fallback_overview += f" is a featured {formatted_genres} film."
    else:
        fallback_overview += " is a popular film from the MovieLens collection."

    poster_url = None
    overview_text = fallback_overview
    rating_val = None
    release_date_val = extracted_year

    tmdb_key = os.getenv("TMDB_API_KEY")
    headers = {"User-Agent": "MovieRec/1.0"}

    # Priority 1: Direct TMDb ID lookup from links.csv (if TMDB_API_KEY is provided)
    tmdb_id = MOVIE_TO_TMDB_MAP.get(movie_id) if movie_id else None

    if tmdb_key and tmdb_id:
        try:
            resp = requests.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"api_key": tmdb_key},
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                poster_path = data.get("poster_path")
                if poster_path:
                    poster_url = TMDB_IMAGE_BASE_URL + poster_path
                if data.get("overview"):
                    overview_text = data.get("overview")
                if data.get("vote_average"):
                    rating_val = data.get("vote_average")
                if data.get("release_date"):
                    release_date_val = data.get("release_date")
        except Exception as err:
            print(f"TMDb ID lookup error for tmdbId={tmdb_id}: {err}")

    # Priority 2: TMDb Title Search
    if tmdb_key and not poster_url and cleaned_title:
        try:
            resp = requests.get(
                f"{TMDB_BASE_URL}/search/movie",
                params={"api_key": tmdb_key, "query": cleaned_title},
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    selected = results[0]
                    if extracted_year:
                        for item in results:
                            if item.get("release_date", "").startswith(extracted_year):
                                selected = item
                                break

                    poster_path = selected.get("poster_path")
                    if poster_path:
                        poster_url = TMDB_IMAGE_BASE_URL + poster_path
                    if selected.get("overview") and overview_text == fallback_overview:
                        overview_text = selected.get("overview")
                    if selected.get("vote_average"):
                        rating_val = selected.get("vote_average")
                    if selected.get("release_date"):
                        release_date_val = selected.get("release_date")
        except Exception as err:
            print(f"TMDb title search error for '{cleaned_title}': {err}")

    # Priority 3: Wikipedia REST API (Free public poster art & overviews)
    if not poster_url or overview_text == fallback_overview:
        wiki_res = fetch_wikipedia_poster_and_overview(cleaned_title, extracted_year)
        if wiki_res:
            if not poster_url and wiki_res.get("poster"):
                poster_url = wiki_res["poster"]
            if overview_text == fallback_overview and wiki_res.get("overview") and len(wiki_res["overview"]) > 20:
                overview_text = wiki_res["overview"]

    result = {
        "overview": overview_text,
        "poster": poster_url,
        "rating": rating_val,
        "release_date": release_date_val,
    }

    TMDB_CACHE[cache_key] = result
    return result


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Movie Recommendation API is running."
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = data.get(
        "username",
        ""
    ).strip()

    password = data.get(
        "password",
        ""
    )

    email = data.get("email", "").strip()

    if not username or not password or not email:
        return jsonify({
            "error": "Username, email, and password are required"
        }), 400

    # Check username
    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        return jsonify({
            "error": "Username already exists"
        }), 409

    # Check email
    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:
        return jsonify({
            "error": "Email already exists"
        }), 409

    # Hash password
    password_hash = (
        bcrypt
        .generate_password_hash(password)
        .decode("utf-8")
    )

    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()

    # Log user in immediately
    session.clear()
    session["user_id"] = user.id

    return jsonify({

        "message": "User registered successfully",

        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

    }), 201


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = data.get(
        "username",
        ""
    ).strip()

    password = data.get(
        "password",
        ""
    )

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if not bcrypt.check_password_hash(
        user.password_hash,
        password
    ):
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    session.clear()

    session["user_id"] = user.id

    print(
        f"User logged in: "
        f"{user.username} "
        f"(id={user.id})"
    )

    return jsonify({

        "message": "Login successful",

        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/me", methods=["GET"])
def current_user():

    user_id = session.get("user_id")

    print(
        f"/me user_id = {user_id}"
    )

    if not user_id:
        return jsonify({
            "logged_in": False
        })

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        session.clear()

        return jsonify({
            "logged_in": False
        })

    return jsonify({

        "logged_in": True,

        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

    })


# =========================================================
# UPDATE SETTINGS
# =========================================================

@app.route("/settings", methods=["PUT"])
def update_settings():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    current_password = data.get("current_password", "")
    new_username = data.get("username", "").strip()
    new_email = data.get("email", "").strip()
    new_password = data.get("new_password", "")

    user = db.session.get(User, user_id)

    if not user:
        session.clear()
        return jsonify({
            "error": "User not found"
        }), 404

    # Verify current password
    if not current_password or not bcrypt.check_password_hash(user.password_hash, current_password):
        return jsonify({
            "error": "Incorrect current password"
        }), 401

    # Validate & update username
    if new_username and new_username != user.username:
        existing = User.query.filter(User.username == new_username, User.id != user_id).first()
        if existing:
            return jsonify({
                "error": "Username is already taken"
            }), 409
        user.username = new_username

    # Validate & update email
    if new_email and new_email != user.email:
        existing = User.query.filter(User.email == new_email, User.id != user_id).first()
        if existing:
            return jsonify({
                "error": "Email is already in use"
            }), 409
        user.email = new_email

    # Update password if provided
    if new_password:
        user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")

    db.session.commit()

    return jsonify({
        "message": "Settings updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.route("/recommend", methods=["GET"])
def recommend():

    movie_title = request.args.get("movie")

    if not movie_title:

        return jsonify({
            "error": "Please provide a movie title."
        }), 400

    print(
        f"\nRecommendation request: "
        f"{movie_title}"
    )

    recommendations = recommend_hybrid(
        movie_title,
        num_recommendations=5
    )

    # Movie not found
    if isinstance(recommendations, str):

        return jsonify({
            "error": recommendations
        }), 404

    enriched_recommendations = []

    for movie in recommendations:

        title = movie["title"]

        tmdb_data = get_tmdb_movie(title, movie_id=movie["movieId"])

        enriched_recommendations.append({

            "movieId": movie["movieId"],

            "title": title,

            "score": movie["score"],

            "overview": tmdb_data["overview"],

            "poster": tmdb_data["poster"],

            "rating": tmdb_data["rating"],

            "release_date": tmdb_data["release_date"]

        })

    return jsonify({

        "movie": movie_title,

        "recommendations":
            enriched_recommendations

    })


# =========================================================
# PERSONALIZED RECOMMENDATIONS (BASED ON WATCHED HISTORY)
# =========================================================

@app.route("/recommend/personalized", methods=["GET"])
def recommend_personalized_endpoint():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "error": "Login required"
        }), 401

    watched_movies = Watched.query.filter_by(user_id=user_id).all()

    if not watched_movies:
        return jsonify({
            "has_watched": False,
            "count": 0,
            "recommendations": []
        })

    watched_ids = [m.movie_id for m in watched_movies]
    raw_recs = recommend_personalized(watched_ids, num_recommendations=10)

    enriched_recommendations = []

    for movie in raw_recs:
        title = movie["title"]
        tmdb_data = get_tmdb_movie(title, movie_id=movie["movieId"])

        enriched_recommendations.append({
            "movieId": movie["movieId"],
            "title": title,
            "score": movie["score"],
            "overview": tmdb_data["overview"],
            "poster": tmdb_data["poster"],
            "rating": tmdb_data["rating"],
            "release_date": tmdb_data["release_date"]
        })

    return jsonify({
        "has_watched": True,
        "count": len(watched_movies),
        "recommendations": enriched_recommendations
    })


# =========================================================
# WATCHLIST - ADD
# =========================================================

@app.route("/watchlist", methods=["POST"])
def add_to_watchlist():

    user_id = session.get("user_id")

    print(
        f"POST /watchlist "
        f"user_id={user_id}"
    )

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    movie_id = data.get("movieId")
    title = data.get("title")

    if movie_id is None or not title:

        return jsonify({
            "error": "movieId and title are required"
        }), 400

    existing = Watchlist.query.filter_by(
        user_id=user_id,
        movie_id=movie_id
    ).first()

    if existing:

        return jsonify({
            "message": "Movie already in watchlist"
        })

    movie = Watchlist(
        user_id=user_id,
        movie_id=movie_id,
        title=title
    )

    db.session.add(movie)
    db.session.commit()

    return jsonify({
        "message": "Movie added to watchlist"
    }), 201


# =========================================================
# WATCHLIST - GET
# =========================================================

@app.route("/watchlist", methods=["GET"])
def get_watchlist():

    user_id = session.get("user_id")

    print(
        f"GET /watchlist "
        f"user_id={user_id}"
    )

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    movies_list = Watchlist.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for movie in movies_list:

        tmdb_data = get_tmdb_movie(
            movie.title,
            movie_id=movie.movie_id
        )

        result.append({

            "movieId": movie.movie_id,

            "title": movie.title,

            "poster": tmdb_data["poster"],

            "overview": tmdb_data["overview"],

            "rating": tmdb_data["rating"],

            "release_date":
                tmdb_data["release_date"]

        })

    return jsonify({
        "watchlist": result
    })


# =========================================================
# WATCHLIST - REMOVE
# =========================================================

@app.route(
    "/watchlist/<int:movie_id>",
    methods=["DELETE"]
)
def remove_from_watchlist(movie_id):

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    movie = Watchlist.query.filter_by(
        user_id=user_id,
        movie_id=movie_id
    ).first()

    if not movie:

        return jsonify({
            "error":
                "Movie not found in watchlist"
        }), 404

    db.session.delete(movie)
    db.session.commit()

    return jsonify({
        "message":
            "Movie removed from watchlist"
    })


# =========================================================
# WATCHED - ADD
# =========================================================

@app.route("/watched", methods=["POST"])
def add_to_watched():

    user_id = session.get("user_id")

    print(
        f"POST /watched "
        f"user_id={user_id}"
    )

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    movie_id = data.get("movieId")
    title = data.get("title")

    if movie_id is None or not title:

        return jsonify({
            "error":
                "movieId and title are required"
        }), 400

    existing = Watched.query.filter_by(
        user_id=user_id,
        movie_id=movie_id
    ).first()

    if existing:

        return jsonify({
            "message":
                "Movie already marked as watched"
        })

    movie = Watched(
        user_id=user_id,
        movie_id=movie_id,
        title=title
    )

    db.session.add(movie)

    # Remove from watchlist
    watchlist_movie = Watchlist.query.filter_by(
        user_id=user_id,
        movie_id=movie_id
    ).first()

    if watchlist_movie:

        db.session.delete(
            watchlist_movie
        )

    db.session.commit()

    return jsonify({
        "message":
            "Movie marked as watched"
    }), 201


# =========================================================
# WATCHED - GET
# =========================================================

@app.route("/watched", methods=["GET"])
def get_watched():

    user_id = session.get("user_id")

    print(
        f"GET /watched "
        f"user_id={user_id}"
    )

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    movies_list = Watched.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for movie in movies_list:

        tmdb_data = get_tmdb_movie(
            movie.title,
            movie_id=movie.movie_id
        )

        result.append({

            "movieId": movie.movie_id,

            "title": movie.title,

            "poster": tmdb_data["poster"],

            "overview": tmdb_data["overview"],

            "rating": tmdb_data["rating"],

            "release_date":
                tmdb_data["release_date"]

        })

    return jsonify({
        "watched": result
    })


# =========================================================
# WATCHED - REMOVE
# =========================================================

@app.route(
    "/watched/<int:movie_id>",
    methods=["DELETE"]
)
def remove_from_watched(movie_id):

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "error": "Login required"
        }), 401

    movie = Watched.query.filter_by(
        user_id=user_id,
        movie_id=movie_id
    ).first()

    if not movie:

        return jsonify({
            "error":
                "Movie not found in watched list"
        }), 404

    db.session.delete(movie)
    db.session.commit()

    return jsonify({
        "message":
            "Movie removed from watched list"
    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
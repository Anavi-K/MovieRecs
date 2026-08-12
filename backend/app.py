from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import os
import re
import time
import requests

from hybrid import recommend_hybrid


# ============================================================
# Flask setup
# ============================================================

app = Flask(__name__)
CORS(app)

load_dotenv()


# ============================================================
# TMDB configuration
# ============================================================

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


# ============================================================
# Persistent HTTP session
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "application/json",
})


# ============================================================
# Extract year from MovieLens title
# ============================================================

def extract_year(title):

    match = re.search(r"\((\d{4})\)", title)

    if match:
        return int(match.group(1))

    return None


# ============================================================
# Clean MovieLens title
# ============================================================

def clean_movie_title(title):

    # Example:
    #
    # Toy Story 2 (1999)
    #
    # becomes:
    #
    # Toy Story 2

    return re.sub(
        r"\s*\(\d{4}\)\s*$",
        "",
        title
    ).strip()


# ============================================================
# Get movie information from TMDB
# ============================================================

def get_tmdb_movie(movie_title):

    if not TMDB_API_KEY:

        print("TMDB_API_KEY not found.")

        return {
            "overview": None,
            "poster": None,
            "rating": None,
            "release_date": None
        }


    # --------------------------------------------------------
    # Prepare title
    # --------------------------------------------------------

    search_title = clean_movie_title(movie_title)

    year = extract_year(movie_title)

    print(f"TMDB search: {search_title}")


    # --------------------------------------------------------
    # Request parameters
    # --------------------------------------------------------

    params = {
        "api_key": TMDB_API_KEY,
        "query": search_title,
        "include_adult": False
    }

    # If we know the year, give TMDB the year too.
    if year:
        params["year"] = year


    url = f"{TMDB_BASE_URL}/search/movie"


    # --------------------------------------------------------
    # Retry request
    # --------------------------------------------------------

    for attempt in range(5):

        try:

            response = session.get(
                url,
                params=params,
                timeout=30
            )


            print(
                f"TMDB status for '{search_title}': "
                f"{response.status_code}"
            )


            # ------------------------------------------------
            # Successful response
            # ------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                results = data.get(
                    "results",
                    []
                )

                print(
                    f"TMDB results for '{search_title}': "
                    f"{len(results)}"
                )


                if not results:

                    return {
                        "overview": None,
                        "poster": None,
                        "rating": None,
                        "release_date": None
                    }


                # ------------------------------------------------
                # Choose best result
                # ------------------------------------------------

                selected = results[0]


                # If year is available, try to find
                # a result with the same release year.

                if year:

                    for result in results:

                        release_date = result.get(
                            "release_date",
                            ""
                        )

                        if release_date.startswith(
                            str(year)
                        ):

                            selected = result
                            break


                # ------------------------------------------------
                # Extract data
                # ------------------------------------------------

                overview = selected.get(
                    "overview"
                )


                poster_path = selected.get(
                    "poster_path"
                )


                if poster_path:

                    poster = (
                        TMDB_IMAGE_BASE_URL
                        + poster_path
                    )

                else:

                    poster = None


                rating = selected.get(
                    "vote_average"
                )


                release_date = selected.get(
                    "release_date"
                )


                return {
                    "overview": overview,
                    "poster": poster,
                    "rating": rating,
                    "release_date": release_date
                }


            # ------------------------------------------------
            # Invalid API key
            # ------------------------------------------------

            elif response.status_code == 401:

                print(
                    "TMDB API key is invalid."
                )

                return {
                    "overview": None,
                    "poster": None,
                    "rating": None,
                    "release_date": None
                }


            # ------------------------------------------------
            # Rate limited
            # ------------------------------------------------

            elif response.status_code == 429:

                print(
                    "TMDB rate limit reached."
                )

                time.sleep(2)

            else:

                print(
                    f"TMDB error "
                    f"{response.status_code}: "
                    f"{response.text[:200]}"
                )

        except requests.exceptions.RequestException as e:

            print(
                f"TMDB request failed for "
                f"'{search_title}' "
                f"(attempt {attempt + 1}/5): "
                f"{e}"
            )

            # Wait before retrying.
            time.sleep(1)


    # --------------------------------------------------------
    # All attempts failed
    # --------------------------------------------------------

    print(
        f"TMDB failed completely for "
        f"'{search_title}'"
    )

    return {
        "overview": None,
        "poster": None,
        "rating": None,
        "release_date": None
    }


# ============================================================
# Recommendation endpoint
# ============================================================

@app.route("/recommend", methods=["GET"])
def recommend():

    movie_title = request.args.get("movie")


    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not movie_title:

        return jsonify({
            "error": "Please provide a movie title."
        }), 400


    print(
        f"\nRecommendation request: "
        f"{movie_title}"
    )


    # --------------------------------------------------------
    # Get hybrid recommendations
    # --------------------------------------------------------

    recommendations = recommend_hybrid(
        movie_title,
        num_recommendations=5
    )


    # --------------------------------------------------------
    # Movie not found
    # --------------------------------------------------------

    if isinstance(
        recommendations,
        str
    ):

        return jsonify({
            "error": recommendations
        }), 404


    # --------------------------------------------------------
    # Add TMDB information
    # --------------------------------------------------------

    enriched_recommendations = []


    for movie in recommendations:

        title = movie["title"]


        # Get information from TMDB
        tmdb_data = get_tmdb_movie(
            title
        )


        enriched_movie = {

            "movieId": movie["movieId"],

            "title": title,

            "score": movie["score"],

            "overview": tmdb_data[
                "overview"
            ],

            "poster": tmdb_data[
                "poster"
            ],

            "rating": tmdb_data[
                "rating"
            ],

            "release_date": tmdb_data[
                "release_date"
            ]
        }


        enriched_recommendations.append(
            enriched_movie
        )


    # --------------------------------------------------------
    # Return JSON
    # --------------------------------------------------------

    return jsonify({

        "movie": movie_title,

        "recommendations":
            enriched_recommendations

    })


# ============================================================
# Home endpoint
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message":
            "Movie Recommendation API is running."
    })


# ============================================================
# Run application
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
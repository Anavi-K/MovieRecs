import { useEffect, useState } from "react";
import MovieCard from "../components/MovieCard";
import "../App.css";

function Discover({
  API_URL,
  watchlist,
  watched,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  onMarkAsWatched,
}) {
  // Search state
  const [movie, setMovie] = useState("");
  const [searchedMovie, setSearchedMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Personalized watched recommendations state
  const [personalizedRecs, setPersonalizedRecs] = useState([]);
  const [personalizedLoading, setPersonalizedLoading] = useState(false);

  // Fetch personalized recommendations based on watched history
  useEffect(() => {
    let isMounted = true;

    const fetchPersonalized = async () => {
      setPersonalizedLoading(true);
      try {
        const response = await fetch(`${API_URL}/recommend/personalized`, {
          credentials: "include",
        });

        if (!response.ok) return;

        const data = await response.json();
        if (isMounted && data.has_watched) {
          setPersonalizedRecs(data.recommendations || []);
        } else if (isMounted) {
          setPersonalizedRecs([]);
        }
      } catch (err) {
        console.error("Error fetching personalized recommendations:", err);
      } finally {
        if (isMounted) setPersonalizedLoading(false);
      }
    };

    fetchPersonalized();

    return () => {
      isMounted = false;
    };
  }, [API_URL, watched]);

  const getRecommendations = async () => {
    if (!movie.trim()) {
      setError("Please enter a movie name.");
      return;
    }

    setLoading(true);
    setError("");
    setRecommendations([]);
    setSearchedMovie("");

    try {
      const response = await fetch(
        `${API_URL}/recommend?movie=${encodeURIComponent(movie.trim())}`,
        {
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Could not get recommendations.");
        return;
      }

      setSearchedMovie(data.movie);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error("Recommendation fetch error:", err);
      setError("Could not connect to the recommendation server.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      getRecommendations();
    }
  };

  return (
    <main className="main">
      {/* Hero / Search Section */}
      <section className="hero">
        <h1>
          What do you want to <span>watch?</span>
        </h1>
        <p>
          Enter a movie you love or explore personalized recommendations based on your watched list.
        </p>

        <div className="search-container">
          <input
            type="text"
            placeholder="Search for a movie (e.g. Toy Story, Inception)..."
            value={movie}
            onChange={(e) => setMovie(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button onClick={getRecommendations} disabled={loading}>
            {loading ? "Finding..." : "Recommend"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {/* Search Loading */}
      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Finding movies you'll love...</p>
        </div>
      )}

      {/* Search Results */}
      {!loading && recommendations.length > 0 && (
        <section className="results">
          <div className="results-header">
            <h2>
              Movies similar to <span>"{searchedMovie}"</span>
            </h2>
            <p>Based on content genres and user ratings</p>
          </div>

          <div className="movie-grid">
            {recommendations.map((movieItem) => (
              <MovieCard
                key={movieItem.movieId}
                movie={movieItem}
                isInWatchlist={watchlist.some(
                  (item) => item.movieId === movieItem.movieId
                )}
                isWatched={watched.some(
                  (item) => item.movieId === movieItem.movieId
                )}
                onAddToWatchlist={onAddToWatchlist}
                onRemoveFromWatchlist={onRemoveFromWatchlist}
                onMarkAsWatched={onMarkAsWatched}
              />
            ))}
          </div>
        </section>
      )}

      {/* Personalized Recommendations Section (Based on Watched List) */}
      <section className="results" style={{ marginTop: "30px" }}>
        <div className="results-header">
          <h2>
            Recommended <span>for You</span>
          </h2>
          <p>Personalized suggestions based on movies you've watched</p>
        </div>

        {personalizedLoading ? (
          <div className="loading" style={{ minHeight: "180px" }}>
            <div className="spinner"></div>
            <p>Analyzing your watch history...</p>
          </div>
        ) : personalizedRecs.length > 0 ? (
          <div className="movie-grid">
            {personalizedRecs.map((movieItem) => (
              <MovieCard
                key={movieItem.movieId}
                movie={movieItem}
                isInWatchlist={watchlist.some(
                  (item) => item.movieId === movieItem.movieId
                )}
                isWatched={watched.some(
                  (item) => item.movieId === movieItem.movieId
                )}
                onAddToWatchlist={onAddToWatchlist}
                onRemoveFromWatchlist={onRemoveFromWatchlist}
                onMarkAsWatched={onMarkAsWatched}
              />
            ))}
          </div>
        ) : (
          <div className="personalized-prompt">
            <span className="prompt-icon">🎬</span>
            <div>
              <h3>No watched movies yet</h3>
              <p>
                Mark movies as watched to unlock personalized recommendations tailored to your taste!
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

export default Discover;
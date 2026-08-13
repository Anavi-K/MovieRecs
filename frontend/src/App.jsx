import { useState } from "react";
import "./App.css";

function App() {
  const [movie, setMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [searchedMovie, setSearchedMovie] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getRecommendations = async () => {
    if (!movie.trim()) {
      setError("Please enter a movie name.");
      return;
    }

    setLoading(true);
    setError("");
    setRecommendations([]);

    try {
      const response = await fetch(
        `https://movierecs-2.onrender.com/recommend?movie=${encodeURIComponent(movie)}`
      );

      if (!response.ok) {
        throw new Error("Failed to get recommendations");
      }

      const data = await response.json();

      if (typeof data === "string") {
        setError(data);
        return;
      }

      if (data.error) {
        setError(data.error);
        return;
      }

      setSearchedMovie(data.movie);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error(err);
      setError(
        "Could not connect to the recommendation server. Make sure Flask is running."
      );
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
    <div className="app">

      {/* Header */}
      <header className="header">
        <div className="logo">
          <span className="logo-icon">🎬</span>
          <span>MovieRec</span>
        </div>

        <p className="tagline">
          Find your next favorite movie
        </p>
      </header>

      {/* Main */}
      <main className="main">

        {/* Hero */}
        <section className="hero">
          <h1>
            What do you want to <span>watch?</span>
          </h1>

          <p>
            Enter a movie you love and we'll recommend similar movies for you to watch.
          </p>

          <div className="search-container">
            <input
              type="text"
              placeholder="Enter a movie name..."
              value={movie}
              onChange={(e) => setMovie(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button
              onClick={getRecommendations}
              disabled={loading}
            >
              {loading ? "Finding..." : "Recommend"}
            </button>
          </div>

          {error && (
            <p className="error">
              {error}
            </p>
          )}
        </section>

        {/* Loading */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Finding movies you'll love...</p>
          </div>
        )}

        {/* Results */}
        {!loading && recommendations.length > 0 && (
          <section className="results">

            <div className="results-header">
              <h2>
                Movies similar to{" "}
                <span>"{searchedMovie}"</span>
              </h2>

              <p>
                Based on content and user ratings
              </p>
            </div>

            <div className="movie-grid">

              {recommendations.map((rec) => (
                <div
                  className="movie-card"
                  key={rec.movieId}
                >

                  {/* Poster */}
                  <div className="poster-container">

                    {rec.poster ? (
                      <img
                        src={rec.poster}
                        alt={rec.title}
                        className="poster"
                      />
                    ) : (
                      <div className="poster-placeholder">
                        <span>🎬</span>
                        <p>No poster available</p>
                      </div>
                    )}

                    <div className="score">
                      {Math.round(rec.score * 100)}% match
                    </div>

                  </div>

                  {/* Movie information */}
                  <div className="movie-info">

                    <h3>{rec.title}</h3>

                    <div className="movie-meta">

                      {rec.release_date && (
                        <span>
                          {rec.release_date.substring(0, 4)}
                        </span>
                      )}

                      {rec.rating !== null && (
                        <span className="rating">
                          ★ {Number(rec.rating).toFixed(1)}
                        </span>
                      )}

                    </div>

                    {rec.overview && (
                      <p className="overview">
                        {rec.overview}
                      </p>
                    )}

                  </div>

                </div>
              ))}

            </div>

          </section>
        )}

        {/* Initial state */}
        {!loading &&
          recommendations.length === 0 &&
          !error && (
            <section className="empty-state">
              <div className="empty-icon">🍿</div>

              <h2>Start discovering</h2>

              <p>
                Search for a movie above to get personalized
                recommendations.
              </p>
            </section>
          )}

      </main>

      {/* Footer */}
      <footer>
        <p>
          MovieRec • Movie Recommendation System
        </p>
      </footer>

    </div>
  );
}

export default App;
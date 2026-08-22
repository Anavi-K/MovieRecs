import { useState } from "react";
import "../App.css";

function MovieCard({
  movie,
  isInWatchlist,
  isWatched,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  onMarkAsWatched,
  onRemoveFromWatched,
}) {
  const [imgError, setImgError] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const MAX_CHARS = 85;
  const overviewText = movie.overview || "";
  const isLongOverview = overviewText.length > MAX_CHARS;

  return (
    <div className="movie-card">
      <div className="poster-container">
        {movie.poster && !imgError ? (
          <img
            src={movie.poster}
            alt={movie.title}
            className="poster"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="poster-placeholder">
            <span style={{ fontSize: "32px", marginBottom: "6px" }}>🎬</span>
            <p style={{ fontWeight: "600", padding: "0 8px", textAlign: "center", fontSize: "12px" }}>
              {movie.title}
            </p>
          </div>
        )}

        {movie.score !== undefined && (
          <div className="score">
            {Math.round(movie.score * 100)}% match
          </div>
        )}
      </div>

      <div className="movie-info">
        <h3 title={movie.title}>{movie.title}</h3>

        <div className="movie-meta">
          {movie.release_date && (
            <span>{String(movie.release_date).substring(0, 4)}</span>
          )}

          {movie.rating !== null && movie.rating !== undefined && (
            <span className="rating">
              ★ {Number(movie.rating).toFixed(1)}
            </span>
          )}
        </div>

        {overviewText && (
          <p className="overview">
            {isLongOverview && !isExpanded
              ? `${overviewText.substring(0, MAX_CHARS)}... `
              : overviewText + " "}

            {isLongOverview && (
              <button
                className="read-more-btn"
                onClick={() => setIsExpanded((prev) => !prev)}
                type="button"
              >
                {isExpanded ? "Show less" : "Read more"}
              </button>
            )}
          </p>
        )}

        {/* Action Buttons */}
        {(onAddToWatchlist ||
          onRemoveFromWatchlist ||
          onMarkAsWatched ||
          onRemoveFromWatched) && (
          <div className="movie-actions">
            {/* Watchlist button */}
            {(onAddToWatchlist || onRemoveFromWatchlist) && !isWatched && (
              <button
                onClick={() =>
                  isInWatchlist
                    ? onRemoveFromWatchlist(movie.movieId)
                    : onAddToWatchlist(movie)
                }
                className="secondary-button"
              >
                {isInWatchlist ? "✓ Saved" : "+ Watchlist"}
              </button>
            )}

            {/* Mark as Watched button */}
            {onMarkAsWatched && (
              <button
                onClick={() => onMarkAsWatched(movie)}
                disabled={isWatched}
                className="primary-button"
              >
                {isWatched ? "✓ Watched" : "Watched"}
              </button>
            )}

            {/* Remove from Watched button */}
            {onRemoveFromWatched && isWatched && (
              <button
                onClick={() => onRemoveFromWatched(movie.movieId)}
                className="secondary-button"
              >
                Remove
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MovieCard;
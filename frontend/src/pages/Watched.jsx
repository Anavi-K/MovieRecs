import MovieCard from "../components/MovieCard";
import "../App.css";

function Watched({ watched, onRemoveFromWatched }) {
  return (
    <main className="main">
      <section className="results page-section">
        <div className="results-header">
          <h1>Watched Movies</h1>
          <p>Movies you've already watched</p>
        </div>

        {watched.length === 0 ? (
          <section className="empty-state">
            <div className="empty-icon">✓</div>
            <h2>No watched movies yet</h2>
            <p>Movies you mark as watched will appear here.</p>
          </section>
        ) : (
          <div className="movie-grid">
            {watched.map((movie) => (
              <MovieCard
                key={movie.movieId}
                movie={movie}
                isInWatchlist={false}
                isWatched={true}
                onRemoveFromWatched={onRemoveFromWatched}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default Watched;
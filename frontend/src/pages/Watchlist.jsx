import MovieCard from "../components/MovieCard";
import "../App.css";

function Watchlist({
  watchlist,
  watched,
  onRemoveFromWatchlist,
  onMarkAsWatched,
}) {
  return (
    <main className="main">
      <section className="results page-section">
        <div className="results-header">
          <h1>My Watchlist</h1>
          <p>Movies you want to watch</p>
        </div>

        {watchlist.length === 0 ? (
          <section className="empty-state">
            <div className="empty-icon">🎬</div>
            <h2>Your watchlist is empty</h2>
            <p>Search for movies in Discover and add them to your watchlist.</p>
          </section>
        ) : (
          <div className="movie-grid">
            {watchlist.map((movie) => (
              <MovieCard
                key={movie.movieId}
                movie={movie}
                isInWatchlist={true}
                isWatched={watched.some(
                  (item) => item.movieId === movie.movieId
                )}
                onRemoveFromWatchlist={onRemoveFromWatchlist}
                onMarkAsWatched={onMarkAsWatched}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default Watchlist;
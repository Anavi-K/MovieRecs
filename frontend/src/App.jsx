import { useEffect, useState } from "react";
import "./App.css";

import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Discover from "./pages/Discover";
import Watchlist from "./pages/Watchlist";
import Watched from "./pages/Watched";
import Settings from "./pages/Settings";

const API_URL = "http://localhost:5000";

function App() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [currentPage, setCurrentPage] = useState("discover");

  const [watchlist, setWatchlist] = useState([]);
  const [watched, setWatched] = useState([]);

  // Check active session
  useEffect(() => {
    fetch(`${API_URL}/me`, { credentials: "include" })
      .then((res) => (res.ok ? res.json() : { logged_in: false }))
      .then((data) => setUser(data.logged_in ? data.user : null))
      .catch(() => setUser(null));
  }, []);

  // Fetch watchlist and watched movies when user is logged in
  useEffect(() => {
    if (!user) return;

    let isMounted = true;

    Promise.all([
      fetch(`${API_URL}/watchlist`, { credentials: "include" }),
      fetch(`${API_URL}/watched`, { credentials: "include" }),
    ])
      .then(async ([watchlistRes, watchedRes]) => {
        if (!isMounted) return;

        if (watchlistRes.ok) {
          const data = await watchlistRes.json();
          setWatchlist(data.watchlist || []);
        }
        if (watchedRes.ok) {
          const data = await watchedRes.json();
          setWatched(data.watched || []);
        }
      })
      .catch((err) => console.error("Error loading user lists:", err));

    return () => {
      isMounted = false;
    };
  }, [user]);

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setCurrentPage("discover");
  };

  const logout = async () => {
    try {
      await fetch(`${API_URL}/logout`, { method: "POST", credentials: "include" });
    } catch (err) {
      console.error("Logout error:", err);
    }
    setUser(null);
    setWatchlist([]);
    setWatched([]);
    setCurrentPage("discover");
    setAuthMode("login");
  };

  const addToWatchlist = async (movie) => {
    try {
      const res = await fetch(`${API_URL}/watchlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ movieId: movie.movieId, title: movie.title }),
      });
      const data = await res.json();
      if (!res.ok) return alert(data.error || "Could not add to watchlist.");
      setWatchlist((prev) => (prev.some((m) => m.movieId === movie.movieId) ? prev : [...prev, movie]));
    } catch {
      alert("Could not connect to server.");
    }
  };

  const removeFromWatchlist = async (movieId) => {
    try {
      const res = await fetch(`${API_URL}/watchlist/${movieId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) return alert("Could not remove movie.");
      setWatchlist((prev) => prev.filter((m) => m.movieId !== movieId));
    } catch (err) {
      console.error(err);
    }
  };

  const markAsWatched = async (movie) => {
    try {
      const res = await fetch(`${API_URL}/watched`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ movieId: movie.movieId, title: movie.title }),
      });
      const data = await res.json();
      if (!res.ok) return alert(data.error || "Could not mark as watched.");
      setWatched((prev) => (prev.some((m) => m.movieId === movie.movieId) ? prev : [...prev, movie]));
      setWatchlist((prev) => prev.filter((m) => m.movieId !== movie.movieId));
    } catch {
      alert("Could not connect to server.");
    }
  };

  const removeFromWatched = async (movieId) => {
    try {
      const res = await fetch(`${API_URL}/watched/${movieId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) return alert("Could not remove movie.");
      setWatched((prev) => prev.filter((m) => m.movieId !== movieId));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="app">
      <Navbar
        user={user}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        logout={logout}
      />

      {!user ? (
        <main className="main">
          {authMode === "login" ? (
            <Login
              API_URL={API_URL}
              onLoginSuccess={handleAuthSuccess}
              onSwitchToSignup={() => setAuthMode("signup")}
            />
          ) : (
            <Signup
              API_URL={API_URL}
              onSignupSuccess={handleAuthSuccess}
              onSwitchToLogin={() => setAuthMode("login")}
            />
          )}
        </main>
      ) : (
        <>
          {currentPage === "discover" && (
            <Discover
              API_URL={API_URL}
              watchlist={watchlist}
              watched={watched}
              onAddToWatchlist={addToWatchlist}
              onRemoveFromWatchlist={removeFromWatchlist}
              onMarkAsWatched={markAsWatched}
            />
          )}

          {currentPage === "watchlist" && (
            <Watchlist
              watchlist={watchlist}
              watched={watched}
              onRemoveFromWatchlist={removeFromWatchlist}
              onMarkAsWatched={markAsWatched}
            />
          )}

          {currentPage === "watched" && (
            <Watched
              watched={watched}
              onRemoveFromWatched={removeFromWatched}
            />
          )}

          {currentPage === "settings" && (
            <Settings
              API_URL={API_URL}
              user={user}
              onUserUpdate={(updatedUser) => setUser(updatedUser)}
            />
          )}
        </>
      )}

      <footer>
        <p>MovieRec • Movie Recommendation System</p>
      </footer>
    </div>
  );
}

export default App;
import { useState, useEffect, useRef } from "react";
import "../App.css";

function Navbar({ user, currentPage, setCurrentPage, logout }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleNavigate = (page) => {
    setCurrentPage(page);
    setDropdownOpen(false);
  };

  const initial = user && user.username ? user.username.charAt(0).toUpperCase() : "U";

  return (
    <header className="header">
      <div
        className="logo"
        style={{ cursor: "pointer" }}
        onClick={() => setCurrentPage("discover")}
      >
        <span className="logo-icon">🎬</span>
        <span>MovieRec</span>
      </div>

      {user ? (
        <div className="profile-container" ref={dropdownRef}>
          <button
            className="profile-button"
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-label="Profile menu"
          >
            <div className="profile-avatar">{initial}</div>
            <span>{user.username}</span>
            <span className={`dropdown-arrow ${dropdownOpen ? "open" : ""}`}>
              ▼
            </span>
          </button>

          {dropdownOpen && (
            <div className="profile-dropdown">
              <div className="dropdown-header">
                <span className="dropdown-user-name">{user.username}</span>
                <span className="dropdown-user-email">
                  {user.email || `${user.username.toLowerCase()}@movierec.local`}
                </span>
              </div>

              <div className="dropdown-divider" />

              <button
                className={`dropdown-item ${currentPage === "watchlist" ? "active" : ""}`}
                onClick={() => handleNavigate("watchlist")}
              >
                <span className="icon">🔖</span> Watchlist
              </button>

              <button
                className={`dropdown-item ${currentPage === "watched" ? "active" : ""}`}
                onClick={() => handleNavigate("watched")}
              >
                <span className="icon">✓</span> Watched
              </button>

              <button
                className={`dropdown-item ${currentPage === "settings" ? "active" : ""}`}
                onClick={() => handleNavigate("settings")}
              >
                <span className="icon">⚙️</span> Settings
              </button>

              <div className="dropdown-divider" />

              <button
                className="dropdown-item logout"
                onClick={() => {
                  setDropdownOpen(false);
                  logout();
                }}
              >
                <span className="icon">🚪</span> Logout
              </button>
            </div>
          )}
        </div>
      ) : (
        <p className="tagline">Find your next favorite movie</p>
      )}
    </header>
  );
}

export default Navbar;
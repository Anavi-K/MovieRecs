import { useState } from "react";
import PasswordInput from "../components/PasswordInput";
import "../App.css";

function Signup({ API_URL, onSignupSuccess, onSwitchToLogin }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!username.trim() || !email.trim() || !password.trim()) {
      setError("Please enter a username, email, and password.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim(),
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Could not register account.");
        return;
      }

      setUsername("");
      setEmail("");
      setPassword("");
      setError("");

      if (onSignupSuccess) {
        onSignupSuccess(data.user);
      }
    } catch (err) {
      console.error("Signup request failed:", err);
      setError("Could not connect to the server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="hero">
      <h1>
        Your movies.
        <br />
        Your <span>recommendations.</span>
      </h1>
      <p>
        Create an account to save movies, track what you've watched, and discover movies you'll love.
      </p>

      <div className="auth-card">
        <h2>Create an account</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <PasswordInput
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <button type="button" onClick={onSwitchToLogin} className="link-button">
            Login
          </button>
        </p>
      </div>
    </section>
  );
}

export default Signup;
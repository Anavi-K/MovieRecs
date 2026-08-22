import { useState } from "react";
import "../App.css";

function Settings({ API_URL, user, onUserUpdate }) {
  const [username, setUsername] = useState(user ? user.username : "");
  const [email, setEmail] = useState(user && user.email ? user.email : "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!currentPassword) {
      setError("Please enter your current password to save changes.");
      return;
    }

    if (newPassword && newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_URL}/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          current_password: currentPassword,
          username: username.trim(),
          email: email.trim(),
          new_password: newPassword || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Could not update settings.");
        return;
      }

      setSuccess("Settings updated successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      if (onUserUpdate) {
        onUserUpdate(data.user);
      }
    } catch (err) {
      console.error("Settings update error:", err);
      setError("Could not connect to the server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="main">
      <section className="results page-section">
        <div className="results-header">
          <h1>Account Settings</h1>
          <p>Manage your profile details and password</p>
        </div>

        <div className="settings-card">
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="settings-section">
              <h3>Profile Information</h3>

              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="settings-section">
              <h3>Change Password</h3>
              <p className="section-help">Leave blank if you don't want to change your password.</p>

              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  placeholder="New password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="settings-section highlight-section">
              <h3>Security Verification</h3>
              <p className="section-help">Enter your current password to authorize updates.</p>

              <div className="form-group">
                <label>Current Password *</label>
                <input
                  type="password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="primary-button settings-submit">
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}

export default Settings;

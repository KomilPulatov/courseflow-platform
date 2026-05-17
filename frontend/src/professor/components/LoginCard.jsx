import { useState } from "react";

export function LoginCard({ onSubmit, loading }) {
  const [email, setEmail] = useState("professor@crsp.example.com");
  const [password, setPassword] = useState("prof12345");

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(email, password);
  }

  return (
    <section className="login-card">
      <h3>Professor Sign In</h3>
      <p className="helper-text">Use the seeded professor account or any professor created by admin.</p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        <button className="button" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </section>
  );
}

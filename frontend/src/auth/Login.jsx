import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [org, setOrg] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!email || !org) return;

    login({ email, org });
    navigate("/app");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
    >
      <div style={{ width: 420 }} className="card">
        {/* ---------- BRAND ---------- */}
        <div
          onClick={() => navigate("/")}
          style={{
            textAlign: "center",
            fontWeight: 700,
            fontSize: 20,
            marginBottom: 20,
            cursor: "pointer"
          }}
        >
          TrustlessProof
        </div>

        <h2 style={{ textAlign: "center" }}>Manager Login</h2>

        <p
          style={{
            color: "#9ca3af",
            marginBottom: 24,
            textAlign: "center"
          }}
        >
          Sign in to access your organization’s trust dashboard.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6 }}>
              Work email
            </label>
            <input
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", marginBottom: 6 }}>
              Organization
            </label>
            <input
              placeholder="e.g. Flipkart"
              value={org}
              onChange={e => setOrg(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>

          <button
            className="primary"
            type="submit"
            disabled={!email || !org}
            style={{ width: "100%" }}
          >
            Continue →
          </button>
        </form>

        <p
          style={{
            marginTop: 18,
            fontSize: 13,
            color: "#94a3b8",
            textAlign: "center"
          }}
        >
          New here?{" "}
          <Link to="/signup" style={{ color: "#9ad" }}>
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}

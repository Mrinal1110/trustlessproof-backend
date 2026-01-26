import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function StartPilot() {
  const [company, setCompany] = useState("");
  const [size, setSize] = useState(3);
  const navigate = useNavigate();

  function startPilot() {
    // 🔴 CRITICAL: reset previous org context
    localStorage.removeItem("pilot_employees");
    localStorage.removeItem("active_employee");

    // create fresh pilot
    localStorage.setItem(
      "pilot",
      JSON.stringify({
        pilot_id: crypto.randomUUID(),
        company,
        size,
        start: new Date().toISOString()
      })
    );

    navigate("/app/pilot/invite");
  }

  return (
    <div style={{ maxWidth: 520 }}>
      <h2>Start a Pilot</h2>

      <p style={{ marginBottom: 24 }}>
        Set up a short pilot to evaluate real-work trust signals across your team.
      </p>

      <div className="card">
        <div style={{ marginBottom: 16 }}>
          <label
            style={{
              display: "block",
              marginBottom: 6,
              fontSize: 14,
              color: "var(--text-muted)"
            }}
          >
            Company name
          </label>

          <input
            placeholder="e.g. Amazon"
            value={company}
            onChange={e => setCompany(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label
            style={{
              display: "block",
              marginBottom: 6,
              fontSize: 14,
              color: "var(--text-muted)"
            }}
          >
            Team size
          </label>

          <input
            type="number"
            min={1}
            value={size}
            onChange={e => setSize(Number(e.target.value))}
            style={{ width: 120 }}
          />
        </div>

        <button
          className="primary"
          disabled={!company}
          onClick={startPilot}
        >
          Start 7-day Pilot →
        </button>
      </div>
    </div>
  );
}

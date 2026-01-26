import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../../config/api";

export default function InviteEmployees() {
  const navigate = useNavigate();

  const [pilot, setPilot] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [name, setName] = useState("");
  const [userId, setUserId] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  /* ---------------- Load pilot context ---------------- */
  useEffect(() => {
    try {
      const pRaw = localStorage.getItem("pilot");
      const eRaw = localStorage.getItem("pilot_employees");

      if (!pRaw) {
        navigate("/app/pilot/start");
        return;
      }

      setPilot(JSON.parse(pRaw));
      setEmployees(eRaw ? JSON.parse(eRaw) : []);
    } catch {
      navigate("/app/pilot/start");
    }
  }, [navigate]);

  /* ---------------- Generate invite ---------------- */
  async function generateInvite() {
    if (!pilot || !userId) return;
    if (employees.length >= pilot.size) return;

    setError(null);
    setLoading(true);

    let token = null;

    // Try backend token (optional but preferred)
    try {
      const res = await fetch(`${API_BASE}/internal/invite-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: pilot.company,
          employee_id: userId,
          expiry_days: 7
        })
      });

      if (!res.ok) {
        throw new Error(`Invite API failed (${res.status})`);
      }

      const data = await res.json();
      token = data.token;
    } catch (err) {
      console.warn("Invite token generation failed:", err.message);
      // Pilot must continue even if backend fails
    }

    const invite = {
      name: name || userId,
      user_id: userId,
      token,
      command: token
        ? `trustlessproof-agent start --token=${token}`
        : `trustlessproof-agent start --user_id=${userId}`,
      created_at: new Date().toISOString()
    };

    const updated = [...employees, invite];
    setEmployees(updated);
    localStorage.setItem("pilot_employees", JSON.stringify(updated));

    setName("");
    setUserId("");
    setLoading(false);
  }

  if (!pilot) return null;

  const limitReached = employees.length >= pilot.size;

  return (
    <div style={{ maxWidth: 760 }}>
      <h2>Invite Employees</h2>

      <p style={{ color: "#9ca3af", marginBottom: 12 }}>
        Pilot for <strong>{pilot.company}</strong> —{" "}
        {employees.length}/{pilot.size} employees invited
      </p>

      <div className="card">
        {limitReached && (
          <p style={{ color: "#facc15", fontSize: 13 }}>
            Employee limit reached for this pilot.
          </p>
        )}

        {error && (
          <p style={{ color: "#f87171", fontSize: 13 }}>
            {error}
          </p>
        )}

        <input
          placeholder="Employee name"
          value={name}
          onChange={e => setName(e.target.value)}
          disabled={limitReached}
          style={{ marginBottom: 8 }}
        />

        <input
          placeholder="Employee ID (e.g. rahul)"
          value={userId}
          onChange={e => setUserId(e.target.value)}
          disabled={limitReached}
        />

        <button
          className="primary"
          style={{ marginTop: 12 }}
          onClick={generateInvite}
          disabled={limitReached || loading}
        >
          {loading ? "Generating…" : "Generate Invite"}
        </button>
      </div>

      {/* ---------------- INVITES LIST ---------------- */}
      {employees.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <h3>Invited Employees</h3>

          {employees.map(e => (
            <div
              key={e.user_id}
              style={{
                marginBottom: 16,
                paddingBottom: 12,
                borderBottom: "1px solid rgba(255,255,255,0.08)"
              }}
            >
              <strong>{e.name}</strong>
              <div style={{ fontSize: 13, color: "#94a3b8" }}>
                ID: {e.user_id}
              </div>

              <code
                style={{
                  display: "block",
                  marginTop: 6,
                  fontSize: 12,
                  background: "#020617",
                  padding: 8,
                  borderRadius: 6
                }}
              >
                {e.command}
              </code>
            </div>
          ))}
        </div>
      )}

      <button
        className="primary"
        style={{ marginTop: 24 }}
        onClick={() => navigate("/app/agents")}
      >
        Continue to Agent Setup →
      </button>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../../config/api";

export default function InviteEmployees() {
  const navigate = useNavigate();

  const [pilot, setPilot] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [name, setName] = useState("");
  const [userId, setUserId] = useState("");
  const [tokens, setTokens] = useState({});

  useEffect(() => {
    const p = localStorage.getItem("pilot");
    if (!p) {
      navigate("/app/pilot/start");
      return;
    }
    setPilot(JSON.parse(p));
  }, [navigate]);

  async function addEmployee() {
    if (!userId || !pilot?.company) return;

    const res = await fetch(`${API_BASE}/internal/invite-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        org_id: pilot.company,
        employee_id: userId,
        expiry_days: 7
      })
    });

    const data = await res.json();

    const updated = [...employees, { name, user_id: userId }];
    setEmployees(updated);
    setTokens(t => ({ ...t, [userId]: data.token }));

    localStorage.setItem("pilot_employees", JSON.stringify(updated));

    setName("");
    setUserId("");
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <h2>Invite Employees</h2>
      <p style={{ color: "#9ca3af" }}>
        Pilot for <strong>{pilot?.company}</strong>
      </p>

      <div className="card">
        <input
          placeholder="Employee name"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ marginBottom: 8 }}
        />
        <input
          placeholder="Employee ID (e.g. rahul)"
          value={userId}
          onChange={e => setUserId(e.target.value)}
        />
        <button
          className="primary"
          style={{ marginTop: 12 }}
          onClick={addEmployee}
        >
          Generate Invite
        </button>
      </div>

      {employees.length > 0 && (
        <div className="card">
          <h3>Invites</h3>

          <ul style={{ listStyle: "none", padding: 0 }}>
            {employees.map(e => (
              <li key={e.user_id} style={{ marginBottom: 16 }}>
                <div><strong>{e.name}</strong></div>
                <div style={{ fontSize: 13, color: "#94a3b8" }}>
                  Activation Token:
                </div>
                <code>{tokens[e.user_id]}</code>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="primary"
        onClick={() => navigate("/app/pilot/status")}
      >
        Continue →
      </button>
    </div>
  );
}

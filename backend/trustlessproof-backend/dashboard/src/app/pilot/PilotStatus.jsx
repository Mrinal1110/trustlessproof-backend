import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = "https://trustlessproof-backend-production.up.railway.app";
// for local dev:
// const API = "http://localhost:8000";

export default function PilotStatus() {
  const navigate = useNavigate();

  const [pilot, setPilot] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [status, setStatus] = useState({});

  /* ---------------- Load pilot + employees ---------------- */
  useEffect(() => {
    const p = localStorage.getItem("pilot");
    const e = localStorage.getItem("pilot_employees");

    if (!p || !e) {
      navigate("/app/pilot/start");
      return;
    }

    setPilot(JSON.parse(p));
    setEmployees(JSON.parse(e));
  }, [navigate]);

  /* ---------------- Fetch trust status ---------------- */
  useEffect(() => {
    if (!employees.length) return;

    employees.forEach(emp => {
      fetch(`${API}/decision/${emp.user_id}`)
        .then(r => r.json())
        .then(data => {
          setStatus(s => ({ ...s, [emp.user_id]: data }));
        })
        .catch(() => {});
    });
  }, [employees]);

  /* ---------------- Pilot ended view ---------------- */
  if (pilot?.ended) {
    return (
      <div className="card" style={{ maxWidth: 720 }}>
        <h2>Pilot Ended</h2>

        <p style={{ color: "#9ca3af", marginBottom: 24 }}>
          This pilot has concluded. No further data is being collected.
        </p>

        <button
          className="primary"
          onClick={() => navigate("/app/pilot/outcome")}
        >
          View Final Outcome →
        </button>
      </div>
    );
  }

  /* ---------------- Active pilot view ---------------- */
  return (
    <div>
      <h2>Pilot Status</h2>

      <p style={{ color: "#9ca3af", marginBottom: 20 }}>
        Company: <strong>{pilot?.company}</strong>
      </p>

      <table style={{ width: "100%", marginBottom: 24 }}>
        <thead>
          <tr>
            <th>Employee</th>
            <th>Trust Status</th>
            <th></th>
          </tr>
        </thead>

        <tbody>
          {employees.map(e => {
            const d = status[e.user_id];
            const band = d?.decision?.band || "low_trust";
            const label = d?.decision?.label || "Low Trust";

            return (
              <tr key={e.user_id}>
                <td>{e.name}</td>

                <td className={`trust-${band}`}>
                  {label}
                </td>

                <td>
                  <button onClick={() => navigate("/app")}>
                    Open Trust Report
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* -------- Outcome CTA -------- */}
      <button
        className="primary"
        onClick={() => navigate("/app/pilot/outcome")}
      >
        View Pilot Outcome →
      </button>
    </div>
  );
}

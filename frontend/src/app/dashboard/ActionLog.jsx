import { useEffect, useState } from "react";

const API = "https://trustlessproof-backend-production.up.railway.app";

export default function ActionLog({ employee }) {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!employee) return;

    fetch(`${API}/action/${employee}`)
      .then(r => r.json())
      .then(data => {
        // backend returns single action object, normalize to list
        setLogs(data ? [data] : []);
      })
      .catch(() => setLogs([]));
  }, [employee]);

  if (!logs.length) {
    return (
      <div className="card">
        <h3>Action Log</h3>
        <p style={{ color: "#9ca3af" }}>
          No trust actions recorded yet.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Action Log</h3>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {logs.map((l, i) => (
          <li key={i} style={{ marginBottom: 14 }}>
            <div style={{ fontWeight: 600 }}>
              {l.message}
            </div>
            <div style={{ fontSize: 12, color: "#94a3b8" }}>
              {new Date(l.evaluated_at).toLocaleString()}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

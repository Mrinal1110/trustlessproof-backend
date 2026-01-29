import { useEffect, useState } from "react";
import { API_BASE } from "../../config/api";

/*
  AgentSetup — Phase 18.3
  ----------------------
  - Shows agent status
  - Shows agent version
  - Shows platform (linux / mac / windows)
  - Safe for mixed fleets
*/

export default function AgentSetup() {
  const [pilot, setPilot] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [status, setStatus] = useState({});

  /* ---------- Load pilot + invited employees ---------- */
  useEffect(() => {
    try {
      const p = JSON.parse(localStorage.getItem("pilot"));
      const e = JSON.parse(localStorage.getItem("pilot_employees")) || [];
      setPilot(p);
      setEmployees(e);
    } catch {
      setPilot(null);
      setEmployees([]);
    }
  }, []);

  /* ---------- Poll agent status ---------- */
  useEffect(() => {
    if (!pilot) return;

    async function fetchStatus() {
      try {
        const r = await fetch(
          `${API_BASE}/agent/status/${pilot.company}`
        );

        if (!r.ok) {
          throw new Error(`Status API failed: ${r.status}`);
        }

        const data = await r.json();
        const map = {};
        data.forEach(row => {
          map[row.employee_id] = row;
        });
        setStatus(map);
      } catch (err) {
        console.error("Agent status fetch failed", err);
        setStatus({});
      }
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, 10_000);
    return () => clearInterval(interval);
  }, [pilot]);

  if (!pilot) {
    return (
      <div className="card">
        <h3>No active pilot</h3>
        <p>Start a pilot to install agents.</p>
      </div>
    );
  }

  function installCommand(emp) {
    if (!emp.token) return null;

    return `curl -sSL https://trustlessproof-agent.vercel.app/install.sh | \\
ORG_ID=${pilot.company} \\
USER_ID=${emp.user_id} \\
TOKEN=${emp.token} \\
bash`;
  }

  function copy(text) {
    navigator.clipboard.writeText(text);
    alert("Install command copied");
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      <h1>Agent Setup</h1>

      <p style={{ color: "#94a3b8", marginBottom: 20 }}>
        Fleet visibility across agent versions and platforms.
      </p>

      {/* ---------- Agents ---------- */}
      <div className="card">
        <h3>Employee Agents</h3>

        <table style={{ width: "100%", marginTop: 16 }}>
          <thead>
            <tr>
              <th align="left">Employee</th>
              <th align="left">Status</th>
              <th align="left">Version</th>
              <th align="left">Platform</th>
              <th align="left">Last Seen</th>
              <th align="left">Install</th>
            </tr>
          </thead>

          <tbody>
            {employees.map(emp => {
              const s = status[emp.user_id];
              const cmd = installCommand(emp);

              return (
                <tr key={emp.user_id}>
                  <td>{emp.name}</td>

                  <td>
                    <AgentBadge state={s?.state} />
                  </td>

                  <td style={{ fontSize: 13 }}>
                    {s?.agent_version || "—"}
                  </td>

                  <td style={{ fontSize: 13, textTransform: "capitalize" }}>
                    {s?.platform || "—"}
                  </td>

                  <td style={{ fontSize: 13, color: "#94a3b8" }}>
                    {s?.expires_at
                      ? new Date(s.expires_at).toLocaleString()
                      : "—"}
                  </td>

                  <td>
                    {!emp.token ? (
                      <div
                        style={{
                          fontSize: 12,
                          color: "#facc15"
                        }}
                      >
                        Invite required
                      </div>
                    ) : (
                      <div
                        style={{
                          background: "#020617",
                          padding: 12,
                          borderRadius: 6,
                          fontSize: 12
                        }}
                      >
                        <code>{cmd}</code>

                        <div
                          style={{
                            marginTop: 8,
                            fontSize: 11,
                            color: "#94a3b8"
                          }}
                        >
                          Token:{" "}
                          <strong>{emp.token}</strong>
                        </div>

                        <button
                          className="primary"
                          style={{
                            fontSize: 12,
                            marginTop: 6
                          }}
                          onClick={() => copy(cmd)}
                        >
                          Copy Install Command
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------- Badge ---------- */

function AgentBadge({ state }) {
  const map = {
    ACTIVE: { label: "Active", color: "#22c55e" },
    OFFLINE: { label: "Offline", color: "#ef4444" },
    EXPIRED: { label: "Expired", color: "#fb923c" }
  };

  const item =
    map[state] || {
      label: "Not Installed",
      color: "#64748b"
    };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        fontSize: 13,
        color: item.color
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: item.color
        }}
      />
      {item.label}
    </span>
  );
}

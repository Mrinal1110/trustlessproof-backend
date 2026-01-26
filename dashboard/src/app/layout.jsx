import { useNavigate, useLocation, useParams } from "react-router-dom";

export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  // Read active employee from URL if present
  const match = location.pathname.match(/^\/app\/employee\/(.+)$/);
  const activeEmployeeId = match ? match[1] : null;

  let pilot = null;
  let employees = [];

  try {
    pilot = JSON.parse(localStorage.getItem("pilot"));
    employees = JSON.parse(localStorage.getItem("pilot_employees")) || [];
  } catch {
    pilot = null;
    employees = [];
  }

  const isPilotStartRoute = location.pathname === "/app/pilot/start";

  function selectEmployee(userId) {
    navigate(`/app/employee/${userId}`);
  }

  return (
    <div className="app-root" style={{ display: "flex", minHeight: "100vh" }}>
      {/* ---------- SIDEBAR ---------- */}
      <aside
        style={{
          width: 240,
          background: "#0b0f1a",
          padding: 20,
          borderRight: "1px solid #222"
        }}
      >
        <h4 style={{ marginBottom: 12 }}>Organization</h4>

        {!pilot && (
          <div style={{ color: "#94a3b8", marginBottom: 16 }}>
            No active pilot
          </div>
        )}

        {pilot && (
          <div style={{ marginBottom: 16 }}>
            <strong>{pilot.company}</strong>
          </div>
        )}

        {/* ---------- EMPLOYEES ---------- */}
        <h4 style={{ marginTop: 24, marginBottom: 8 }}>Employees</h4>

        {!pilot && (
          <div style={{ fontSize: 13, color: "#64748b" }}>
            Start a pilot to invite employees.
          </div>
        )}

        {pilot && employees.length === 0 && (
          <div style={{ fontSize: 13, color: "#64748b" }}>
            No employees invited yet.
          </div>
        )}

        {pilot &&
          employees.map(e => {
            const isActive = activeEmployeeId === e.user_id;

            return (
              <div
                key={e.user_id}
                onClick={() => selectEmployee(e.user_id)}
                style={{
                  padding: "6px 10px",
                  marginTop: 6,
                  borderRadius: 6,
                  fontSize: 14,
                  cursor: "pointer",
                  background: isActive ? "#1f2937" : "transparent",
                  color: isActive ? "#fff" : "#c7d2fe"
                }}
              >
                {e.name}
              </div>
            );
          })}

        {/* ---------- ADMIN ---------- */}
        <h4 style={{ marginTop: 32, marginBottom: 8 }}>Admin</h4>

        {pilot && (
          <>
            <div
              style={{ cursor: "pointer", marginBottom: 6, fontSize: 14 }}
              onClick={() => navigate("/app/agents")}
            >
              Agent Setup
            </div>

            <div
              style={{ cursor: "pointer", fontSize: 14 }}
              onClick={() => navigate("/app/pilot/status")}
            >
              Pilot Status
            </div>
          </>
        )}
      </aside>

      {/* ---------- MAIN ---------- */}
      <main className="app-main" style={{ flex: 1, padding: 32 }}>
        {!pilot && !isPilotStartRoute ? (
          <div className="card" style={{ maxWidth: 720 }}>
            <h2>No active pilot</h2>

            <p style={{ color: "#94a3b8", marginBottom: 20 }}>
              Start a pilot to invite employees and begin trust verification.
            </p>

            <button
              className="primary"
              onClick={() => navigate("/app/pilot/start")}
            >
              Start Pilot →
            </button>
          </div>
        ) : (
          children
        )}
      </main>
    </div>
  );
}

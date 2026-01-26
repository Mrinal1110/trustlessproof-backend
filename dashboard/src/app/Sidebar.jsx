import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Sidebar({ pilot }) {
  const navigate = useNavigate();

  const [employees, setEmployees] = useState([]);
  const [activeEmployee, setActiveEmployee] = useState(null);

  /* ---------- Load employees ---------- */
  useEffect(() => {
    try {
      const raw = localStorage.getItem("pilot_employees");
      const list = raw ? JSON.parse(raw) : [];
      setEmployees(Array.isArray(list) ? list : []);
    } catch {
      setEmployees([]);
    }
  }, []);

  /* ---------- Restore active employee ---------- */
  useEffect(() => {
    const saved = localStorage.getItem("active_employee");
    if (saved) setActiveEmployee(saved);
  }, []);

  function selectEmployee(emp) {
    // persist
    localStorage.setItem("active_employee", emp.user_id);

    // local highlight
    setActiveEmployee(emp.user_id);

    // 🔴 CRITICAL: notify dashboard immediately
    window.dispatchEvent(new Event("employee-change"));

    // ensure route
    navigate("/app");
  }

  return (
    <aside
      style={{
        width: 240,
        background: "#0b0f1a",
        padding: 20,
        borderRight: "1px solid #222",
        color: "#fff"
      }}
    >
      {/* ---------- ORG ---------- */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 6 }}>
          Organization
        </div>
        <div style={{ fontWeight: 600 }}>
          {pilot?.company || "No active pilot"}
        </div>
      </div>

      {/* ---------- EMPLOYEES ---------- */}
      <div style={{ marginBottom: 28 }}>
        <h3 style={{ fontSize: 14, marginBottom: 10 }}>
          Employees
        </h3>

        {employees.length === 0 && (
          <div style={{ fontSize: 13, color: "#64748b" }}>
            No employees invited yet
          </div>
        )}

        {employees.map(emp => (
          <div
            key={emp.user_id}
            onClick={() => selectEmployee(emp)}
            style={{
              cursor: "pointer",
              padding: "8px 10px",
              marginBottom: 6,
              borderRadius: 6,
              background:
                activeEmployee === emp.user_id
                  ? "#1f2937"
                  : "transparent"
            }}
          >
            {emp.name || emp.user_id}
          </div>
        ))}
      </div>

      {/* ---------- ADMIN ---------- */}
      <div>
        <h3 style={{ fontSize: 14, marginBottom: 10 }}>
          Admin
        </h3>

        <div
          style={linkStyle}
          onClick={() => navigate("/app/agents")}
        >
          Agent Setup
        </div>

        <div
          style={linkStyle}
          onClick={() => navigate("/app/pilot/status")}
        >
          Pilot Status
        </div>
      </div>
    </aside>
  );
}

const linkStyle = {
  cursor: "pointer",
  fontSize: 14,
  color: "#9ca3af",
  marginBottom: 8
};

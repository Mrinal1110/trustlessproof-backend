import { useNavigate } from "react-router-dom";
import { useOrg } from "./context/OrgContext";

/*
  Sidebar — FINAL
  ----------------
  - One row per employee (deduped upstream)
  - Clear status labels (Active / Inactive / Offline)
  - No historical noise
*/

const stateLabel = {
  ACTIVE: { text: "Active", color: "#22c55e" },
  STALE: { text: "Inactive", color: "#facc15" },
  EXPIRED: { text: "Offline", color: "#64748b" }
};

export default function Sidebar() {
  const navigate = useNavigate();
  const {
    agents,
    activeAgent,
    setActiveAgent,
    loading,
    error
  } = useOrg();

  function selectAgent(agent) {
    setActiveAgent(agent);
    navigate(`/app/employee/${agent.user_id}`);
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
      <h3 style={{ fontSize: 14, marginBottom: 12 }}>
        Active Agents
      </h3>

      {loading && (
        <div style={{ fontSize: 13, color: "#64748b" }}>
          Loading agents…
        </div>
      )}

      {error && (
        <div style={{ fontSize: 13, color: "#f87171" }}>
          Failed to load agents
        </div>
      )}

      {!loading && agents.length === 0 && (
        <div style={{ fontSize: 13, color: "#64748b" }}>
          No agents detected.
        </div>
      )}

      {agents.map(agent => {
        const isActive =
          activeAgent?.user_id === agent.user_id;

        const meta =
          stateLabel[agent.state] ||
          stateLabel.EXPIRED;

        return (
          <div
            key={agent.user_id}
            onClick={() => selectAgent(agent)}
            style={{
              cursor: "pointer",
              padding: "8px 10px",
              marginBottom: 6,
              borderRadius: 6,
              background: isActive
                ? "#1f2937"
                : "transparent",
              color: isActive
                ? "#fff"
                : "#c7d2fe"
            }}
          >
            <div>{agent.user_id}</div>

            <div
              style={{
                fontSize: 11,
                marginTop: 2,
                color: meta.color
              }}
            >
              {meta.text}
            </div>
          </div>
        );
      })}

      <div style={{ marginTop: 32 }}>
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
          onClick={() =>
            navigate("/app/pilot/status")
          }
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

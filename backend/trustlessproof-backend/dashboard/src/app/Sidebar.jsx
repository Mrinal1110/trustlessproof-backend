import React from "react";
import { Link } from "react-router-dom";

export default function Sidebar({ selected, onSelect }) {
  const users = ["Test User", "Rahul"];

  return (
    <aside
      style={{
        width: "240px",
        background: "#111",
        borderRight: "1px solid #222",
        padding: "20px",
      }}
    >
      <h3 style={{ color: "#fff", marginBottom: "16px" }}>Team</h3>

      {users.map((user) => (
        <div
          key={user}
          onClick={() => onSelect(user)}
          style={{
            padding: "10px",
            marginBottom: "6px",
            cursor: "pointer",
            borderRadius: "6px",
            background: selected === user ? "#222" : "transparent",
            color: "#fff",
          }}
        >
          {user}
        </div>
      ))}

      <div style={{ marginTop: "24px", fontSize: "14px" }}>
        <Link to="/app" style={{ color: "#9ad" }}>Dashboard</Link><br />
        <Link to="/app/pilot/start" style={{ color: "#9ad" }}>Pilot</Link>
      </div>
    </aside>
  );
}

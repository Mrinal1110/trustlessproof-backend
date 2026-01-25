import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import AppLayout from "./layout";

function getPilotInfo() {
  try {
    const raw = localStorage.getItem("pilot");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function AppShell() {
  const [employee, setEmployee] = useState("test_user");
  const [pilot, setPilot] = useState(null);

  useEffect(() => {
    setPilot(getPilotInfo());
  }, []);

  const dayNumber = pilot
    ? Math.max(
        1,
        Math.ceil(
          (Date.now() - new Date(pilot.start).getTime()) /
            (1000 * 60 * 60 * 24)
        )
      )
    : null;

  return (
    <>
      {/* ================= PILOT CONTEXT BAR ================= */}
      {pilot && (
        <div
          style={{
            position: "sticky",
            top: 0,
            zIndex: 200,
            background: "rgba(15, 23, 42, 0.9)",
            backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            padding: "10px 24px",
            fontSize: 13,
            color: "#c7d2fe"
          }}
        >
          <strong>Pilot Active</strong>
          {" · "}
          {pilot.company}
          {" · "}
          {pilot.size} Employees
          {" · "}
          Day {dayNumber} of 7
        </div>
      )}

      <AppLayout employee={employee} setEmployee={setEmployee}>
        <Outlet context={{ employee }} />
      </AppLayout>
    </>
  );
}

import { useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import AppLayout from "./layout";

export default function AppShell() {
  const navigate = useNavigate();
  const { session, org, logout } = useAuth();

  /* -------------------------------------------------
     ORG ENFORCEMENT (CRITICAL)
     ------------------------------------------------- */
  useEffect(() => {
    if (!session || !org) return;

    const rawPilot = localStorage.getItem("pilot");
    if (!rawPilot) return;

    try {
      const pilot = JSON.parse(rawPilot);

      // If pilot org !== auth org → reset pilot safely
      if (pilot.company !== org) {
        console.warn(
          "Org mismatch detected. Resetting pilot context.",
          pilot.company,
          "→",
          org
        );

        localStorage.removeItem("pilot");
        localStorage.removeItem("pilot_employees");
        localStorage.removeItem("active_employee");

        navigate("/app/pilot/start", { replace: true });
      }
    } catch {
      // Corrupt pilot data → wipe
      localStorage.removeItem("pilot");
      localStorage.removeItem("pilot_employees");
      localStorage.removeItem("active_employee");
    }
  }, [session, org, navigate]);

  /* -------------------------------------------------
     PILOT CONTEXT BAR (AUTH-AWARE)
     ------------------------------------------------- */
  let pilot = null;
  try {
    pilot = JSON.parse(localStorage.getItem("pilot"));
  } catch {
    pilot = null;
  }

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
      {/* -------- TOP CONTEXT BAR -------- */}
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 300,
          background: "rgba(15, 23, 42, 0.92)",
          backdropFilter: "blur(8px)",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          padding: "10px 24px",
          fontSize: 13,
          color: "#c7d2fe",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}
      >
        <div>
          <strong>{org}</strong>
          {pilot && (
            <>
              {" · "}
              Pilot Active
              {" · "}
              {pilot.size} Employees
              {" · "}
              Day {dayNumber} of 7
            </>
          )}
        </div>

        <button
          onClick={() => {
            logout();
            navigate("/login", { replace: true });
          }}
          style={{
            background: "none",
            border: "none",
            color: "#93c5fd",
            cursor: "pointer",
            fontSize: 13
          }}
        >
          Logout
        </button>
      </div>

      {/* -------- APP LAYOUT -------- */}
      <AppLayout>
        <Outlet />
      </AppLayout>
    </>
  );
}

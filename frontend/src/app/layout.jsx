import Sidebar from "./Sidebar";
import { useLocation } from "react-router-dom";
import { Outlet } from "react-router-dom";

export default function AppLayout() {
  const location = useLocation();

  const isPilotStartRoute =
    location.pathname === "/app/pilot/start";

  return (
    <div
      className="app-root"
      style={{ display: "flex", minHeight: "100vh" }}
    >
      {/* ---------- SIDEBAR ---------- */}
      <Sidebar />

      {/* ---------- MAIN ---------- */}
      <main
        className="app-main"
        style={{ flex: 1, padding: 32 }}
      >
        <Outlet />
      </main>
    </div>
  );
}

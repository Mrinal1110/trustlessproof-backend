import React from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import "./index.css";

/* ---------- Auth ---------- */
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import Login from "./auth/Login";
import Signup from "./auth/Signup";

/* ---------- Marketing ---------- */
import Landing from "./marketing/Landing";

/* ---------- App ---------- */
import AppShell from "./app/AppShell";
import Dashboard from "./app/dashboard/Dashboard";

/* ---------- Pilot ---------- */
import StartPilot from "./app/pilot/StartPilot";
import InviteEmployees from "./app/pilot/InviteEmployees";
import PilotStatus from "./app/pilot/PilotStatus";
import PilotOutcome from "./app/pilot/PilotOutcome";

/* ---------- Agents ---------- */
import AgentSetup from "./app/agents/AgentSetup";

/* ---------- Route Guards ---------- */

function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return children;
}

function RedirectIfAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/app" replace />;

  return children;
}

/* ---------- App Root ---------- */

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* -------- Public -------- */}
          <Route path="/" element={<Landing />} />

          <Route
            path="/login"
            element={
              <RedirectIfAuth>
                <Login />
              </RedirectIfAuth>
            }
          />

          <Route
            path="/signup"
            element={
              <RedirectIfAuth>
                <Signup />
              </RedirectIfAuth>
            }
          />

          {/* -------- Protected App -------- */}
          <Route
            path="/app"
            element={
              <RequireAuth>
                <AppShell />
              </RequireAuth>
            }
          >
            <Route index element={<Dashboard />} />

            {/* ✅ URL-based employee route */}
            <Route path="employee/:employeeId" element={<Dashboard />} />

            <Route path="pilot/start" element={<StartPilot />} />
            <Route path="pilot/invite" element={<InviteEmployees />} />
            <Route path="pilot/status" element={<PilotStatus />} />
            <Route path="pilot/outcome" element={<PilotOutcome />} />

            <Route path="agents" element={<AgentSetup />} />
          </Route>

          {/* -------- Fallback -------- */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);

import "./index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Landing from "./marketing/Landing";
import AppShell from "./app/AppShell";

import PilotOutcome from "./app/pilot/PilotOutcome";
import Dashboard from "./app/dashboard/Dashboard";
import StartPilot from "./app/pilot/StartPilot";
import InviteEmployees from "./app/pilot/InviteEmployees";
import PilotStatus from "./app/pilot/PilotStatus";

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Landing />} />

      <Route path="/app" element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="pilot/outcome" element={<PilotOutcome />} />
        <Route path="pilot/start" element={<StartPilot />} />
        <Route path="pilot/invite" element={<InviteEmployees />} />
        <Route path="pilot/status" element={<PilotStatus />} />
      </Route>
    </Routes>
  </BrowserRouter>
);

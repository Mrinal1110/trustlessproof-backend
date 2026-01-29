import { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "../../auth/AuthProvider";

const OrgContext = createContext(null);

const API = "https://trustlessproof-backend-production.up.railway.app";

/*
  OrgContext — FINAL CANONICAL VERSION
  -----------------------------------
  - Uses authenticated org ONLY
  - Deduplicates agents by employee_id
  - Prefers ACTIVE > STALE > EXPIRED
  - Provides clean agent list to UI
*/

export function OrgProvider({ children }) {
  const { org } = useAuth();

  const [agents, setAgents] = useState([]);
  const [activeAgent, setActiveAgent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!org) return;

    let cancelled = false;

    async function fetchAgents() {
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API}/agent/status/${org}`);
        if (!res.ok) {
          throw new Error(`Agent status fetch failed (${res.status})`);
        }

        const data = await res.json();
        if (cancelled) return;

        // ---- DEDUPLICATION LOGIC ----
        const priority = {
          ACTIVE: 3,
          STALE: 2,
          EXPIRED: 1
        };

        const byEmployee = {};

        for (const row of Array.isArray(data) ? data : []) {
          const id = row.employee_id;

          if (
            !byEmployee[id] ||
            priority[row.state] >
              priority[byEmployee[id].state]
          ) {
            byEmployee[id] = {
              user_id: row.employee_id,
              state: row.state,
              last_seen: row.last_heartbeat,
              session_id: row.session_id || null
            };
          }
        }

        const list = Object.values(byEmployee);
        setAgents(list);

        // Auto-select first available agent
        if (!activeAgent && list.length > 0) {
          setActiveAgent(list[0]);
        }

        // Clear selection if active agent disappears
        if (
          activeAgent &&
          !list.find(
            a => a.user_id === activeAgent.user_id
          )
        ) {
          setActiveAgent(list[0] || null);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("OrgContext error:", err);
          setError(err.message);
          setAgents([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchAgents();
    const interval = setInterval(fetchAgents, 10_000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [org]);

  return (
    <OrgContext.Provider
      value={{
        org,
        agents,
        activeAgent,
        setActiveAgent,
        loading,
        error
      }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() {
  const ctx = useContext(OrgContext);
  if (!ctx) {
    throw new Error(
      "useOrg must be used inside <OrgProvider>"
    );
  }
  return ctx;
}

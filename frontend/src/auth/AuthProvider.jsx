import { createContext, useContext, useEffect, useState } from "react";

/*
  AuthProvider (Phase 11A)
  -----------------------
  - Frontend-only auth scaffold
  - No backend calls yet
  - Persists session in localStorage
  - Locks app to a single org per manager
*/

const AuthContext = createContext(null);

const STORAGE_KEY = "tp_auth_session";

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  /* ---------- Restore session on load ---------- */
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setSession(JSON.parse(raw));
      }
    } catch {
      setSession(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /* ---------- Persist session ---------- */
  useEffect(() => {
    if (session) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [session]);

  /* ---------- Mock login (Phase 11A) ---------- */
  function login({ email, org }) {
    // In Phase 11A, we mock auth.
    // Backend verification will replace this later.
    const mockSession = {
      manager_id: crypto.randomUUID(),
      email,
      org, // authoritative org for this manager
      token: `mock_${crypto.randomUUID()}`,
      created_at: new Date().toISOString()
    };

    setSession(mockSession);
  }

  /* ---------- Logout ---------- */
  function logout() {
    setSession(null);

    // Clear Phase-10 scoped data safely
    localStorage.removeItem("pilot");
    localStorage.removeItem("pilot_employees");
    localStorage.removeItem("active_employee");
  }

  const value = {
    loading,
    isAuthenticated: !!session,
    session,
    org: session?.org || null,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/* ---------- Hook ---------- */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

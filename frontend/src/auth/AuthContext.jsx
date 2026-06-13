import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

// The seeded demo accounts (passwords are dev-only, from the backend bootstrap).
// We log them all in up front so the floating role-switcher can jump between
// dashboards instantly during the live demo — every token is a REAL JWT.
export const IDENTITIES = [
  { key: "admin", role: "admin", username: "admin", password: "admin123", label: "Exam Controller" },
  { key: "cust1", role: "custodian", username: "cust1", password: "custodian1", label: "Custodian · Registrar" },
  { key: "cust2", role: "custodian", username: "cust2", password: "custodian2", label: "Custodian · Controller" },
  { key: "cust3", role: "custodian", username: "cust3", password: "custodian3", label: "Custodian · Dean" },
  { key: "cust4", role: "custodian", username: "cust4", password: "custodian4", label: "Custodian · Vigilance" },
  { key: "cust5", role: "custodian", username: "cust5", password: "custodian5", label: "Custodian · Board Sec." },
  { key: "cand001", role: "candidate", username: "cand001", password: "candidate1", label: "Candidate R-001" },
  { key: "cand002", role: "candidate", username: "cand002", password: "candidate2", label: "Candidate R-002" },
  { key: "investigator", role: "investigator", username: "investigator", password: "invest123", label: "Forensic Investigator" },
];

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [sessions, setSessions] = useState({}); // username -> { token, me, ...identity }
  // Initial dashboard can be deep-linked: ?id=cust2 (exact identity) or
  // ?role=candidate (first identity of that role). Defaults to admin.
  const [activeKey, setActiveKey] = useState(() => {
    if (typeof window === "undefined") return "admin";
    const p = new URLSearchParams(window.location.search);
    const byId = IDENTITIES.find((i) => i.key === p.get("id"));
    if (byId) return byId.key;
    const byRole = IDENTITIES.find((i) => i.role === p.get("role"));
    if (byRole) return byRole.key;
    return "admin";
  });
  const [status, setStatus] = useState("connecting"); // connecting | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Log identities in sequentially: avoids a thundering herd of parallel
        // auth requests against the dev server, and makes StrictMode's double
        // mount harmless. Each session is published as it completes so the UI
        // can render the active dashboard without waiting for all nine.
        for (const id of IDENTITIES) {
          const { access_token } = await api.login(id.username, id.password);
          const me = await api.get("/auth/me", access_token);
          if (cancelled) return;
          setSessions((prev) => ({
            ...prev,
            [id.username]: { ...id, token: access_token, me },
          }));
          if (status !== "ready") setStatus("ready");
        }
      } catch (e) {
        if (cancelled) return;
        setError(e);
        setStatus("error");
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(() => {
    const active =
      sessions[
        IDENTITIES.find((i) => i.key === activeKey)?.username || "admin"
      ] || null;
    return {
      status,
      error,
      sessions,
      identities: IDENTITIES,
      active,
      activeKey,
      role: active?.role,
      token: active?.token,
      setActiveKey,
    };
  }, [sessions, activeKey, status, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

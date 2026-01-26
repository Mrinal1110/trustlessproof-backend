import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE } from "../../config/api";

import ActionLog from "./ActionLog";
import TrustSummary from "./TrustSummary";
import TrustVerdict from "./TrustVerdict";
import ConfidenceChart from "./ConfidenceChart";
import PolicyPanel from "./PolicyPanel";
import PilotControls from "./PilotControls";

export default function Dashboard() {
  const { employeeId } = useParams();

  const [decision, setDecision] = useState(null);
  const [proofs, setProofs] = useState([]);
  const [loading, setLoading] = useState(false);

  /* ---------- Fetch employee data ---------- */
  useEffect(() => {
    if (!employeeId) return;

    setLoading(true);

    Promise.all([
      fetch(`${API_BASE}/decision/${employeeId}`).then(r => r.json()),
      fetch(`${API_BASE}/proofs/${employeeId}`).then(r => r.json())
    ])
      .then(([decisionData, proofsData]) => {
        setDecision({
          band: decisionData?.decision?.band,
          label: decisionData?.decision?.label,
          action: decisionData?.decision?.action,
          explanation: decisionData?.decision?.explanation,
          policy: decisionData?.decision?.policy,
          confidence: decisionData?.session_confidence,
          windows: decisionData?.windows
        });

        setProofs(
          Array.isArray(proofsData)
            ? proofsData.filter(p => p.user_id === employeeId)
            : []
        );
      })
      .finally(() => setLoading(false));
  }, [employeeId]);

  /* ---------- Empty states ---------- */
  if (!employeeId) {
    return (
      <div className="card">
        <h3>No employee selected</h3>
        <p>Select an employee from the sidebar to view trust details.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="card">Loading employee data…</div>;
  }

  return (
    <div>
      <h1>Employee Trust Report</h1>
      <h2 style={{ color: "#9ca3af" }}>{employeeId}</h2>

      <TrustVerdict decision={decision} />
      <PolicyPanel decision={decision} />
      <TrustSummary decision={decision} />
      <ActionLog employee={employeeId} />
      <PilotControls />
      <ConfidenceChart proofs={proofs} />
    </div>
  );
}

import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { API_BASE } from "../../config/api";

import ActionLog from "./ActionLog";
import TrustSummary from "./TrustSummary";
import TrustVerdict from "./TrustVerdict";
import ConfidenceChart from "./ConfidenceChart";
import PolicyPanel from "./PolicyPanel";
import PilotControls from "./PilotControls";

export default function Dashboard() {
  const { employee } = useOutletContext();

  const [decision, setDecision] = useState(null);
  const [proofs, setProofs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!employee) return;

    setLoading(true);

    Promise.all([
      fetch(`${API_BASE}/decision/${employee}`).then(r => r.json()),
      fetch(`${API_BASE}/proofs/${employee}`).then(r => r.json())
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
            ? proofsData.filter(p => p.user_id === employee)
            : []
        );
      })
      .finally(() => setLoading(false));
  }, [employee]);

  if (!employee) return <div className="card">Select an employee</div>;
  if (loading) return <div className="card">Loading employee data…</div>;

  return (
    <div>
      <h1>Employee Dashboard</h1>
      <h2 style={{ color: "#9ca3af" }}>{employee}</h2>

      <TrustVerdict decision={decision} />
      <PolicyPanel decision={decision} />
      <TrustSummary decision={decision} />
      <ActionLog employee={employee} />
      <PilotControls />
      <ConfidenceChart proofs={proofs} />
    </div>
  );
}

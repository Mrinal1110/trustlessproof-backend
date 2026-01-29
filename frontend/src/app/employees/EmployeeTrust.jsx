import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { API_BASE } from "../../config/api";
import TrustVerdict from "./TrustVerdict";
import TrustSummary from "./TrustSummary";

export default function EmployeeTrust() {
  const { id: employeeId } = useParams();

  const [decision, setDecision] = useState(null);
  const [proofs, setProofs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!employeeId) return;

    async function load() {
      try {
        const [d, p] = await Promise.all([
          fetch(`${API_BASE}/decision/${employeeId}`).then(r => r.json()),
          fetch(`${API_BASE}/proofs/${employeeId}`).then(r => r.json()),
        ]);

        setDecision(d);
        setProofs(Array.isArray(p) ? p : []);
      } catch (e) {
        console.error("Employee load failed", e);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [employeeId]);

  if (loading) {
    return <div className="card">Loading employee report…</div>;
  }

  if (!decision) {
    return (
      <div className="card">
        <h3>No data</h3>
        <p>No trust data available for this employee yet.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <h1>Employee Trust Report</h1>
      <p style={{ color: "#94a3b8" }}>{employeeId}</p>

      <TrustVerdict decision={decision} />
      <TrustSummary decision={decision} proofs={proofs} />
    </div>
  );
}

import { useEffect, useState } from "react";
import { API_BASE } from "../../config/api";

export default function PilotOutcome() {
  const [data, setData] = useState(null);
  const pilot = JSON.parse(localStorage.getItem("pilot"));

  useEffect(() => {
    if (!pilot?.company) return;

    fetch(`${API_BASE}/pilot/outcome/${pilot.company}`)
      .then(r => r.json())
      .then(setData);
  }, [pilot]);

  if (!pilot) return <div className="card">No pilot found.</div>;
  if (!data) return <div className="card">Loading pilot outcome…</div>;

  return (
    <div style={{ maxWidth: 900 }}>
      <h1>Pilot Outcome</h1>
      <p style={{ color: "#9ca3af" }}>Company: {data.org_id}</p>

      <div className="card">
        <h2>Executive Summary</h2>
        <p>{data.executive_summary}</p>
      </div>

      <div className="card">
        <h2>Overview</h2>
        <p>Employees evaluated: {data.employees_evaluated}</p>
        <p>Average confidence: {data.average_confidence}</p>
      </div>

      <div className="card">
        <h2>Trust Distribution</h2>
        <ul>
          {Object.entries(data.band_distribution).map(([band, count]) => (
            <li key={band}>
              {band.replace("_", " ")}: {count}
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2>Employee Results</h2>
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Band</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map(r => (
              <tr key={r.employee_id}>
                <td>{r.employee_id}</td>
                <td>{r.band}</td>
                <td>{r.confidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button
        className="primary"
        onClick={() =>
          window.open(`${API_BASE}/pilot/export/${pilot.company}`, "_blank")
        }
      >
        Download CSV Report
      </button>

      <div className="card" style={{ marginTop: 32 }}>
        <h2>Next Steps</h2>
        <p>
          This pilot has concluded. To continue trust monitoring
          without interruption, convert this pilot into a paid plan.
        </p>

        <ul style={{ color: "#9ca3af" }}>
          <li>No surveillance</li>
          <li>No screen or keystroke tracking</li>
          <li>Continuous trust signals</li>
          <li>Exportable reports</li>
        </ul>

        <button
          className="primary"
          style={{ marginTop: 16 }}
          onClick={() =>
            window.location.href =
              "mailto:founders@trustlessproof.com?subject=Convert Pilot to Paid"
          }
        >
          Convert Pilot → Paid
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { API_BASE } from "../../config/api";

function downloadCSV(rows, filename) {
  const header = ["Employee ID", "Name", "Trust Band", "Confidence"];
  const csv = [
    header.join(","),
    ...rows.map(r =>
      [
        r.employee_id,
        `"${r.name}"`,
        r.band,
        r.confidence.toFixed(3)
      ].join(",")
    )
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function PilotOutcome() {
  const pilotRaw = localStorage.getItem("pilot");
  const employeesRaw = localStorage.getItem("pilot_employees");

  if (!pilotRaw || !employeesRaw) {
    return (
      <div className="card">
        <h2>No pilot data</h2>
        <p>Unable to load pilot outcome.</p>
      </div>
    );
  }

  const pilot = JSON.parse(pilotRaw);
  const employees = JSON.parse(employeesRaw);

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const rows = [];

      for (const e of employees) {
        try {
          const r = await fetch(
            `${API_BASE}/decision/${e.user_id}`
          );
          const d = await r.json();

          rows.push({
            employee_id: e.user_id,
            name: e.name,
            band: d?.decision?.band || "unknown",
            confidence: d?.session_confidence ?? 0
          });
        } catch {
          rows.push({
            employee_id: e.user_id,
            name: e.name,
            band: "unknown",
            confidence: 0
          });
        }
      }

      setResults(rows);
      setLoading(false);
    }

    load();
  }, [employees]);

  if (loading) {
    return <div className="card">Calculating pilot outcome…</div>;
  }

  const avg =
    results.reduce((s, r) => s + r.confidence, 0) /
    (results.length || 1);

  return (
    <div style={{ maxWidth: 900 }}>
      <h1>Pilot Outcome</h1>

      <p style={{ color: "#9ca3af" }}>
        Company: <strong>{pilot.company}</strong>
      </p>

      <div className="card">
        <h2>Executive Summary</h2>
        <p>
          This pilot evaluated real-work trust signals across{" "}
          {results.length} employees over a 7-day period.
        </p>
        <p>
          Average confidence score:{" "}
          <strong>{avg.toFixed(3)}</strong>
        </p>
      </div>

      <div className="card">
        <h2>Employee Results</h2>

        <table style={{ width: "100%" }}>
          <thead>
            <tr>
              <th align="left">Employee</th>
              <th align="left">Trust Band</th>
              <th align="left">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {results.map(r => (
              <tr key={r.employee_id}>
                <td>{r.name}</td>
                <td>{r.band}</td>
                <td>{r.confidence.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <button
          className="primary"
          style={{ marginTop: 16 }}
          onClick={() =>
            downloadCSV(
              results,
              `trustlessproof-pilot-${pilot.company}.csv`
            )
          }
        >
          Download CSV Report
        </button>
      </div>

      <div className="card" style={{ marginTop: 24 }}>
        <h2>Next Steps</h2>
        <p>
          This pilot has completed successfully. To continue trust
          monitoring without interruption, convert this pilot into a
          paid plan.
        </p>

        <button
          className="primary"
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

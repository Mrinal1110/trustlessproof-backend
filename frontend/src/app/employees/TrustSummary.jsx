export default function TrustSummary({ decision, proofs }) {
  if (!decision) return null;

  const windows = decision.windows || {};

  return (
    <div className="card">
      <h3>Assessment Summary</h3>

      <div style={{ marginTop: 12 }}>
        {Object.entries(windows).map(([key, w]) => (
          <div
            key={key}
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "6px 0",
              borderBottom: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <span style={{ textTransform: "capitalize" }}>
              {key} window
            </span>
            <span>
              avg {w.average?.toFixed(3)} ({w.samples} samples)
            </span>
          </div>
        ))}
      </div>

      {proofs?.length > 0 && (
        <p style={{ marginTop: 12, opacity: 0.6 }}>
          Total proofs collected: {proofs.length}
        </p>
      )}
    </div>
  );
}


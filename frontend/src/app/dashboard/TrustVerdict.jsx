export default function TrustVerdict({ decision }) {
  if (!decision) return null;

  const bandMap = {
    normal: {
      label: "Normal",
      color: "#22c55e",
      action: "Continue normal access",
    },
    insufficient_data: {
      label: "Insufficient Data",
      color: "#facc15",
      action: "Continue observation",
    },
    low_trust: {
      label: "Low Trust Detected",
      color: "#ef4444",
      action: "Restrict access and investigate",
    },
  };

  const band = bandMap[decision.band] || bandMap.insufficient_data;
  const windows = decision.windows || {};

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <h2 style={{ marginBottom: 12 }}>Trust Assessment</h2>

      <div
        style={{
          fontSize: 22,
          fontWeight: 600,
          color: band.color,
          marginBottom: 12,
        }}
      >
        {band.label}
      </div>

      <div style={{ marginBottom: 6 }}>
        <strong>Recommended action:</strong>{" "}
        {band.action}
      </div>

      <div style={{ marginBottom: 6 }}>
        <strong>Confidence level:</strong>{" "}
        {decision.confidence != null
          ? `${Math.round(decision.confidence * 100)}%`
          : "N/A"}
      </div>

      <div>
        <strong>Analysis windows:</strong>{" "}
        {Object.keys(windows).length
          ? Object.keys(windows).join(", ")
          : "N/A"}
      </div>
    </div>
  );
}

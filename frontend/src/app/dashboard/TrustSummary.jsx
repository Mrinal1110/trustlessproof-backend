export default function TrustSummary({ decision }) {
  if (!decision) {
    return (
      <div className="card">
        <h3>Assessment Summary</h3>
        <p>No trust data available yet.</p>
      </div>
    );
  }

  const windows = decision.windows || {};

  return (
    <div className="card">
      <h3>Assessment Summary</h3>

      <p>
        <strong>Status:</strong>{" "}
        <span style={{ textTransform: "capitalize" }}>
          {decision.band || "unknown"}
        </span>
      </p>

      <p>
        <strong>Confidence score:</strong>{" "}
        {decision.confidence != null
          ? decision.confidence.toFixed(3)
          : "N/A"}
      </p>

      <p>
        <strong>Windows analyzed:</strong>{" "}
        {Object.keys(windows).length
          ? Object.keys(windows).join(", ")
          : "N/A"}
      </p>

      {decision.explanation && (
        <p
          style={{
            marginTop: 12,
            color: "#94a3b8",
            lineHeight: 1.6,
          }}
        >
          {decision.explanation}
        </p>
      )}
    </div>
  );
}


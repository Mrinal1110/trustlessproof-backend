export default function TrustVerdict({ decision }) {
  if (!decision) return null;

  return (
    <div className="card">
      <h2
        style={{
          color:
            decision.band === "low_trust"
              ? "#ef4444"
              : decision.band === "high_trust"
              ? "#22c55e"
              : "#facc15",
        }}
      >
        {decision.label}
      </h2>

      {decision.confidence !== null && (
        <p>Confidence score: {decision.confidence.toFixed(3)}</p>
      )}

      {/* ✅ DO NOT RENDER decision.windows HERE */}
    </div>
  );
}

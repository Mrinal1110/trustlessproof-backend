export default function PilotControls() {
  return (
    <div className="card">
      <h3>Pilot Controls</h3>

      <p style={{ color: "#94a3b8", lineHeight: 1.6 }}>
        This pilot runs in <strong>observation-only mode</strong>.
        No automatic enforcement, access restriction, or device control
        is performed by TrustlessProof.
      </p>

      <p style={{ fontSize: 13, color: "#64748b" }}>
        All trust signals are evaluated server-side and reported
        transparently at the end of the pilot.
      </p>
    </div>
  );
}

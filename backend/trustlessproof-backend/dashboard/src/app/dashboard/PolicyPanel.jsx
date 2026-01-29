export default function PolicyPanel({ decision }) {
  if (!decision?.policy) return null;

  const policyMap = {
    full_access: {
      label: "Full Access",
      description: "No restrictions. Work may proceed normally."
    },
    monitor: {
      label: "Passive Monitoring",
      description: "Activity is observed without intervention."
    },
    review_required: {
      label: "Manager Review Required",
      description: "Delegation or sensitive actions should be reviewed."
    },
    restricted: {
      label: "Restricted",
      description: "Access limitations are recommended pending review."
    }
  };

  const policy = policyMap[decision.policy];

  return (
    <div className="card">
      <h3>Trust Policy (Pilot)</h3>

      <p>
        <strong>Policy state:</strong>{" "}
        <span style={{ fontWeight: 600 }}>
          {policy?.label || decision.policy}
        </span>
      </p>

      {policy?.description && (
        <p
          style={{
            marginTop: 8,
            color: "#94a3b8",
            lineHeight: 1.6
          }}
        >
          {policy.description}
        </p>
      )}

      <p
        style={{
          marginTop: 14,
          fontSize: 12,
          color: "#64748b"
        }}
      >
        This policy is declarative only. No automatic enforcement is active
        during the pilot.
      </p>
    </div>
  );
}

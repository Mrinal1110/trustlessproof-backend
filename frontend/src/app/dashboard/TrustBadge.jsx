export default function TrustBadge({ verdict }) {
  const map = {
    low: { label: "Low Trust", color: "var(--low)" },
    probable: { label: "Probable", color: "var(--probable)" },
    high: { label: "High Trust", color: "var(--high)" }
  };

  const item = map[verdict] || map.low;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        fontWeight: 500,
        color: item.color
      }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: item.color
        }}
      />
      {item.label}
    </span>
  );
}

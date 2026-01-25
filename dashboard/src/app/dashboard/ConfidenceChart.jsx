import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function ConfidenceChart({ proofs }) {
  if (!proofs || proofs.length === 0) {
    return <div>No proof data yet.</div>;
  }

  const data = proofs.map((p, i) => ({
    index: i + 1,
    confidence: p.confidence
  }));

  return (
    <div style={{ height: 300 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="index" />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="confidence"
            stroke="#6d6aff"
            strokeWidth={2}
            dot
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

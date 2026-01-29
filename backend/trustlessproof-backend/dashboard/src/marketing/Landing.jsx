import HowItWorks3D from "../HowItWorks3D";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

/* ---------------- DEMO DATA (STATIC, SAFE) ---------------- */

const demoDecision = {
  session_confidence: 0.47,
  windows: 4,
  decision: {
    band: "probable",
    label: "Probable",
    explanation: "Work is likely genuine with minor irregularities."
  }
};

const demoProofs = [
  { id: 1, confidence: 0.38 },
  { id: 2, confidence: 0.22 },
  { id: 3, confidence: 0.61 },
  { id: 4, confidence: 0.47 }
];

/* ---------------------------------------------------------- */

export default function Landing() {
  const navigate = useNavigate();

  const [show3D, setShow3D] = useState(false);

  const sectionsRef = useRef([]);
  const liveRef = useRef(null);

  /* ---------------- Scroll reveal ---------------- */
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries =>
        entries.forEach(
          e => e.isIntersecting && e.target.classList.add("visible")
        ),
      { threshold: 0.15 }
    );

    sectionsRef.current.forEach(el => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const reveal = el => {
    if (el && !sectionsRef.current.includes(el)) {
      sectionsRef.current.push(el);
    }
  };

  const scrollToLive = () => {
    liveRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const trustBand = demoDecision.decision.band;

  return (
    <div className="app-root marketing-bg">
      {/* ================= HEADER ================= */}
      <header className="header">
        <div className="header-brand">
          <h1>TrustlessProof</h1>
          <span className="header-tagline">
            Trustless Proof of Human Effort
          </span>
        </div>

        <nav className="header-nav">
          <button onClick={() => setShow3D(true)}>How it works</button>
          <button onClick={scrollToLive}>Live proof</button>

          <button
            className="nav-cta"
            onClick={() => navigate("/app/pilot/start")}
          >
            Start Pilot
          </button>
        </nav>
      </header>

      {/* ================= HERO ================= */}
      <section ref={reveal} className="section hero-split reveal">
        <div>
          <h2 className="hero-title">
            Work.<br />Proven.<br />Not Watched.
          </h2>

          <p className="hero-subtitle">
            Cryptographic proof of real human effort — built for trust,
            not surveillance.
          </p>

          <button
            className="hero-cta"
            onClick={() => navigate("/app/pilot/start")}
          >
            Start 7-Day Pilot
          </button>

          <div style={{ marginTop: 18 }}>
            <button
              style={{
                background: "none",
                border: "none",
                color: "#9ca3af",
                cursor: "pointer",
                fontSize: 14
              }}
              onClick={scrollToLive}
            >
              Watch Trust Emerge →
            </button>
          </div>
        </div>

        <div className="trust-visual">
          <div className="node">Activity</div>
          <div className="line" />
          <div className="node mid">Proof</div>
          <div className="line" />
          <div className="node target">Trust</div>
        </div>
      </section>

      {/* ================= INTRO ================= */}
      <section ref={reveal} className="section narrow reveal">
        <h3>What is TrustlessProof?</h3>
        <p className="long-text">
          TrustlessProof is a local-first verification system that proves
          real human work occurred — without recording screens,
          keystrokes, or content.
        </p>
        <p className="long-text">
          Instead of asking <em>“What did you do?”</em>, it answers:
          <strong> “Did real work happen?”</strong>
        </p>
      </section>

      {/* ================= WHY ================= */}
      <section ref={reveal} className="section narrow reveal">
        <h3>Why this exists</h3>
        <p className="long-text">
          Remote work broke traditional trust mechanisms. Surveillance
          filled the gap — at the cost of privacy, morale, and accuracy.
        </p>
        <p className="long-text">
          TrustlessProof is built on a different assumption:
          <strong> trust should be verified, not enforced.</strong>
        </p>
      </section>

      {/* ================= DEMO KPIs ================= */}
      <section ref={reveal} className="section reveal">
        <div className="kpi-grid">
          <div className="card">
            <h4>Session Confidence</h4>
            <div className="metric">
              {demoDecision.session_confidence.toFixed(2)}
            </div>
          </div>

          <div className="card">
            <h4>Trust Classification</h4>
            <div className={`metric small trust-${trustBand}`}>
              {demoDecision.decision.label}
            </div>
            <p>{demoDecision.decision.explanation}</p>
          </div>

          <div className="card">
            <h4>Verified Windows</h4>
            <div className="metric">{demoDecision.windows}</div>
          </div>
        </div>
      </section>

      {/* ================= DEMO CHART ================= */}
      <section
        ref={el => {
          reveal(el);
          liveRef.current = el;
        }}
        className="section narrow analytics reveal"
      >
        <h3>Confidence Over Time</h3>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={demoProofs}>
              <XAxis dataKey="id" />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="confidence"
                stroke="#6366f1"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <p style={{ marginTop: 12, fontSize: 13, color: "#94a3b8" }}>
          Example trust signal shown for illustration purposes.
        </p>
      </section>

      {/* ================= PRIVACY ================= */}
      <section ref={reveal} className="section narrow reveal">
        <h3>Privacy & Ethics</h3>
        <p className="long-text">
          TrustlessProof never records screens, keystrokes, audio,
          messages, or content. All analysis happens locally.
        </p>
        <p className="long-text">
          Only cryptographic proofs and numerical signals leave the
          device — making it suitable for high-trust environments.
        </p>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="footer">
        <span>© TrustlessProof</span>
        <span>Zero-knowledge productivity proof for remote teams</span>
      </footer>

      {/* ================= 3D OVERLAY ================= */}
      {show3D && <HowItWorks3D onClose={() => setShow3D(false)} />}
    </div>
  );
}

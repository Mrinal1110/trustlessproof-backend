import { useEffect, useRef, useState } from "react";

const SLIDES = [
  {
    title: "The Problem",
    text:
      "Remote work broke trust. Surveillance replaced leadership with screenshots, webcams, and fear."
  },
  {
    title: "The Insight",
    text:
      "Managers don’t need activity. They need confidence that real human effort happened."
  },
  {
    title: "The Shift",
    text:
      "TrustlessProof verifies effort — not behavior — using cryptographic continuity."
  },
  {
    title: "How It Works",
    text:
      "Local agent → effort signals → hash chain → server verification → confidence."
  },
  {
    title: "The Outcome",
    text:
      "Trust without surveillance. Privacy without excuses. Proof without policing."
  }
];

export default function HowItWorks3D({ onClose }) {
  const [index, setIndex] = useState(0);
  const sceneRef = useRef(null);

  // 3D mouse tilt
  useEffect(() => {
    const handleMouse = e => {
      const scene = sceneRef.current;
      if (!scene) return;

      const x = (e.clientX / window.innerWidth - 0.5) * 12;
      const y = (e.clientY / window.innerHeight - 0.5) * -12;

      scene.style.transform = `
        perspective(1800px)
        rotateX(${y}deg)
        rotateY(${x}deg)
      `;
    };

    window.addEventListener("mousemove", handleMouse);
    return () => window.removeEventListener("mousemove", handleMouse);
  }, []);

  const next = () =>
    setIndex(i => Math.min(i + 1, SLIDES.length - 1));
  const prev = () =>
    setIndex(i => Math.max(i - 1, 0));

  return (
    <div style={overlay}>
      <button style={close} onClick={onClose}>✕</button>

      {/* LEFT ARROW — only if NOT first slide */}
      {index > 0 && (
        <div style={{ ...navZone, left: 0 }} onClick={prev}>
          <div style={navArrow}>‹</div>
        </div>
      )}

      {/* RIGHT ARROW — only if NOT last slide */}
      {index < SLIDES.length - 1 && (
        <div style={{ ...navZone, right: 0 }} onClick={next}>
          <div style={navArrow}>›</div>
        </div>
      )}

      <div ref={sceneRef} style={scene}>
        {SLIDES.map((s, i) => {
          const offset = i - index;
          const active = offset === 0;

          return (
            <div
              key={i}
              style={{
                ...card,
                transform: `
                  translate(-50%, -50%)
                  translateZ(${active ? 160 : -Math.abs(offset) * 220}px)
                  scale(${active ? 1 : 0.85})
                `,
                opacity: Math.abs(offset) > 2 ? 0 : 1,
                zIndex: 30 - Math.abs(offset)
              }}
            >
              <h1 style={title}>{s.title}</h1>
              <p style={text}>{s.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ================= STYLES ================= */

const overlay = {
  position: "fixed",
  inset: 0,
  background:
    "radial-gradient(circle at center, rgba(99,102,241,0.18), transparent 60%), #020617",
  zIndex: 9999,
  overflow: "hidden"
};

const scene = {
  position: "absolute",
  inset: 0,
  transformStyle: "preserve-3d",
  transition: "transform 0.18s ease-out"
};

const card = {
  position: "absolute",
  top: "50%",
  left: "50%",
  width: "70%",
  maxWidth: 900,
  padding: "64px",
  borderRadius: 28,
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))",
  backdropFilter: "blur(18px)",
  boxShadow:
    "0 100px 220px rgba(0,0,0,0.75), inset 0 0 0 1px rgba(255,255,255,0.08)",
  color: "#e5e7eb",
  transformStyle: "preserve-3d",
  transition: "all 0.75s cubic-bezier(0.22,1,0.36,1)"
};

const title = {
  fontSize: 48,
  marginBottom: 28,
  letterSpacing: "-0.8px"
};

const text = {
  fontSize: 22,
  lineHeight: 1.7,
  color: "#c7d2fe"
};

const close = {
  position: "absolute",
  top: 28,
  right: 36,
  fontSize: 28,
  background: "none",
  border: "none",
  color: "#9ca3af",
  cursor: "pointer",
  zIndex: 10000
};

/* ---- Navigation ---- */

const navZone = {
  position: "absolute",
  top: 0,
  bottom: 0,
  width: "14%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
  zIndex: 9000
};

const navArrow = {
  width: 64,
  height: 64,
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: 36,
  color: "#e0e7ff",
  background: "rgba(255,255,255,0.06)",
  backdropFilter: "blur(12px)",
  boxShadow: "0 0 40px rgba(99,102,241,0.35)",
  transition: "all 0.25s ease"
};

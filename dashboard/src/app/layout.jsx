export default function AppLayout({ employee, setEmployee, children }) {
  return (
    <div className="app-root" style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 220,
          background: "#0b0f1a",
          padding: 20,
          borderRight: "1px solid #222",
        }}
      >
        <h3>Team</h3>

        <div
          onClick={() => setEmployee("test_user")}
          style={{
            cursor: "pointer",
            padding: "6px 10px",
            marginTop: 8,
            borderRadius: 6,
            background: employee === "test_user" ? "#1f2937" : "transparent",
          }}
        >
          Test User
        </div>

        <div
          onClick={() => setEmployee("rahul")}
          style={{
            cursor: "pointer",
            padding: "6px 10px",
            marginTop: 8,
            borderRadius: 6,
            background: employee === "rahul" ? "#1f2937" : "transparent",
          }}
        >
          Rahul
        </div>
      </aside>

      <main className="app-main">{children}</main>
    </div>
  );
}

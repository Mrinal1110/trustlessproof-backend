export default function EmployeeSelector({ employees, active, onSelect }) {
  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {employees.map(e => (
        <li
          key={e.user_id}
          onClick={() => onSelect(e)}
          style={{
            padding: "8px 12px",
            cursor: "pointer",
            background:
              active?.user_id === e.user_id ? "#333" : "transparent"
          }}
        >
          {e.name}
        </li>
      ))}
    </ul>
  );
}

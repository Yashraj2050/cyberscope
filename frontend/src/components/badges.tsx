

export function StatusBadge({ status }: { status: "OBSERVED" | "INFERRED" | "UNKNOWN" }) {
  return (
    <span className={`badge badge-${status.toLowerCase()}`}>
      {status}
    </span>
  );
}

export function ConfidenceBadge({ level }: { level: "HIGH" | "MEDIUM" | "LOW" }) {
  return (
    <span className={`badge badge-unknown`} style={{ border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>
      EVIDENCE STRENGTH: {level}
    </span>
  );
}

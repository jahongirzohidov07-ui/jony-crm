import { StudentIcon } from "./StudentIcon";

/** The shield face is above the centre of its sprite cell. Keep text anchored to the face. */
export function StudentLevelBadge({ level, size = 86 }: { level?: string; size?: number }) {
  return <span className="student-level-badge" role="img" aria-label={`Daraja: ${level || "—"}`} style={{ width: size, height: size }}>
    <StudentIcon name="level" size={size} />
    <span aria-hidden="true" className="student-level-badge-label" style={{ fontSize: size * 0.29 }}>{level || "—"}</span>
  </span>;
}

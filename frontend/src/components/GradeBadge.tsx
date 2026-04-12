import './GradeBadge.css'

interface Props {
  grade: number | null;
  maxScore: number | null;
  hasGrades: boolean;
  gradedAssignments: number;
  totalAssignments: number;
  loading?: boolean;
}

export default function GradeBadge(props: Props) {
  // Loading state
  if (props.loading) {
    return (
      <div className="GradeBadge GradeBadge--loading">
        <div className="GradeBadge__placeholder" />
      </div>
    )
  }

  // No grades state
  if (!props.hasGrades || props.grade === null || props.maxScore === null) {
    return (
      <div className="GradeBadge GradeBadge--empty">
        <span className="GradeBadge__label">No grades yet</span>
      </div>
    )
  }

  // Grade available state
  const percentage = (props.grade / props.maxScore) * 100
  const colorClass = percentage >= 80 ? "green" : percentage >= 60 ? "yellow" : "red"
  const isPartial = props.gradedAssignments < props.totalAssignments

  return (
    <div className={`GradeBadge GradeBadge--${colorClass}`}>
      <div className="GradeBadge__score">
        <span className="GradeBadge__grade">{props.grade.toFixed(1)}</span>
        <span className="GradeBadge__separator"> / </span>
        <span className="GradeBadge__max">{props.maxScore}</span>
      </div>
      {isPartial && (
        <span className="GradeBadge__partial">
          {props.gradedAssignments} of {props.totalAssignments} graded
        </span>
      )}
    </div>
  )
}

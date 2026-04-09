import './AssignmentCard.css'

interface Props {
  onClick?: () => void
  children?: React.ReactNode
  id: number | string
  dueDate?: string | null
}

// ── Status badge logic ────────────────────────────────────────────────────────

type Status = 'Upcoming' | 'Active' | 'Past Due' | 'No Date'

function getStatus(dueDate?: string | null): Status {
  if (!dueDate) return 'No Date'
  const now = new Date()
  const due = new Date(dueDate)
  if (isNaN(due.getTime())) return 'No Date'
  if (due < now) return 'Past Due'
  // Active if due within the next 7 days, Upcoming otherwise
  const sevenDays = 7 * 24 * 60 * 60 * 1000
  return due.getTime() - now.getTime() <= sevenDays ? 'Active' : 'Upcoming'
}

function formatDueDate(dueDate: string): string {
  const due = new Date(dueDate)
  if (isNaN(due.getTime())) return ''
  return due.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function AssignmentCard(props: Props) {
  const status = getStatus(props.dueDate)

  return (
    <div
      onClick={() => {
        window.location.href = `/assignments/${props.id}`
      }}
      className="A_Card"
    >
      <img src="/icons/document.svg" alt="document" />

      <div className="A_Card__body">
        <span className="A_Card__name">{props.children}</span>

        <div className="A_Card__meta">
          {/* Due date */}
          <span className="A_Card__due">
            {props.dueDate
              ? `Due ${formatDueDate(props.dueDate)}`
              : 'No due date'}
          </span>

          {/* Status badge */}
          <span className={`A_Card__badge A_Card__badge--${status.toLowerCase().replace(' ', '-')}`}>
            {status}
          </span>
        </div>
      </div>
    </div>
  )
}

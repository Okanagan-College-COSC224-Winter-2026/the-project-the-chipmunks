import './CompletionRing.css';

interface Props {
  pct: number;
  submitted: number;
  total: number;
}

export default function CompletionRing({ pct, submitted, total }: Props) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;

  // Crimson when low, sienna when mid, green when high (semantic)
  const colour = pct >= 75 ? '#2e7d32' : pct >= 40 ? '#BA7792' : '#E10054';

  return (
    <div className="CompletionRing">
      <svg width="140" height="140" viewBox="0 0 140 140">
        {/* Background track */}
        <circle
          cx="70" cy="70" r={r}
          fill="none" stroke="#D2BAC3" strokeWidth="12"
        />
        {/* Progress arc */}
        <circle
          cx="70" cy="70" r={r}
          fill="none"
          stroke={colour}
          strokeWidth="12"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
        {/* Percentage label */}
        <text
          x="70" y="64"
          textAnchor="middle"
          fontSize="22"
          fontWeight="bold"
          fill={colour}
        >
          {pct}%
        </text>
        {/* Submitted / total */}
        <text
          x="70" y="84"
          textAnchor="middle"
          fontSize="12"
          fill="#764D5D"
        >
          {submitted}/{total}
        </text>
      </svg>
      <p className="CompletionRing__label">Submission Rate</p>
    </div>
  );
}

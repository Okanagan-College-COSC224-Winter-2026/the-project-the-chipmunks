import './ScoreBar.css'

interface Props {
  avgScore: number;
  maxScore: number;
}

export default function ScoreBar(props: Props) {
  const percentage = props.maxScore > 0
    ? (props.avgScore / props.maxScore) * 100
    : 0

  // Color coding: red < 50%, yellow 50-75%, green > 75%
  const colorClass = percentage >= 75 ? "green" : percentage >= 50 ? "yellow" : "red"

  return (
    <div className="ScoreBar">
      <div className="ScoreBar__track">
        <div
          className={`ScoreBar__fill ScoreBar__fill--${colorClass}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <span className={`ScoreBar__text ScoreBar__text--${colorClass}`}>
        {props.avgScore.toFixed(1)} / {props.maxScore}
      </span>
    </div>
  )
}

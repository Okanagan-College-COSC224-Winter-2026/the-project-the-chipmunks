import './ScoreInput.css'

interface Props {
  value: number | null;
  maxScore: number;
  onChange: (value: number) => void;
}

export default function ScoreInput(props: Props) {
  const percentage = props.value !== null ? (props.value / props.maxScore) * 100 : 0;

  return (
    <div className="ScoreInput">
      <input
        type="range"
        min={0}
        max={props.maxScore}
        value={props.value ?? 0}
        onChange={(e) => props.onChange(Number(e.target.value))}
        className="ScoreInput-slider"
        style={{
          background: `linear-gradient(to right, var(--button-primary) ${percentage}%, var(--background-secondary) ${percentage}%)`
        }}
      />
      <span className="ScoreInput-display">
        {props.value ?? 0} / {props.maxScore}
      </span>
    </div>
  )
}

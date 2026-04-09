import './CriterionCard.css';

export interface CriterionData {
  id?: number;
  name: string;
  description: string;
  max_score: number;
  weight: number;
  position: number;
}

interface Props {
  criterion: CriterionData;
  index: number;
  onChange: (index: number, field: keyof CriterionData, value: string | number) => void;
  onDelete: (index: number) => void;
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
  isFirst: boolean;
  isLast: boolean;
}

export default function CriterionCard({
  criterion, index, onChange, onDelete, onMoveUp, onMoveDown, isFirst, isLast,
}: Props) {
  return (
    <div className="criterion-card">
      <div className="criterion-header">
        <span className="criterion-number">#{index + 1}</span>
        <div className="criterion-move-btns">
          <button disabled={isFirst} onClick={() => onMoveUp(index)} title="Move up">{'\u2191'}</button>
          <button disabled={isLast} onClick={() => onMoveDown(index)} title="Move down">{'\u2193'}</button>
        </div>
        <button className="criterion-delete" onClick={() => onDelete(index)}>{'\u2715'}</button>
      </div>
      <div className="criterion-fields">
        <label>
          Name
          <input
            value={criterion.name}
            onChange={e => onChange(index, 'name', e.target.value)}
            placeholder="e.g. Communication"
          />
        </label>
        <label>
          Description
          <textarea
            value={criterion.description}
            onChange={e => onChange(index, 'description', e.target.value)}
            rows={2}
            placeholder="Describe what this criterion evaluates..."
          />
        </label>
        <div className="criterion-row">
          <label>
            Max Score
            <input
              type="number" min={1} max={100}
              value={criterion.max_score}
              onChange={e => onChange(index, 'max_score', parseInt(e.target.value) || 1)}
            />
          </label>
          <label>
            Weight (%)
            <input
              type="number" min={0} max={100} step={0.5}
              value={criterion.weight}
              onChange={e => onChange(index, 'weight', parseFloat(e.target.value) || 0)}
            />
          </label>
        </div>
      </div>
    </div>
  );
}
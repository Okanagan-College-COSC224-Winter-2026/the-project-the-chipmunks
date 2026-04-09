import { useState } from 'react'
import ScoreInput from './ScoreInput'
import Button from './Button'
import './RubricForm.css'

interface Props {
  criteria: RubricCriteria[];
  onSubmit: (scores: Record<number, number>, comments: Record<number, string>) => void;
  disabled?: boolean;
}

export default function RubricForm(props: Props) {
  const [scores, setScores] = useState<Record<number, number>>({});
  const [comments, setComments] = useState<Record<number, string>>({});

  const scoredCriteria = props.criteria.filter(c => c.has_score);
  const allScored = scoredCriteria.every(c => scores[c.id] !== undefined);

  const handleScoreChange = (criteriaId: number, value: number) => {
    setScores(prev => ({ ...prev, [criteriaId]: value }));
  };

  const handleCommentChange = (criteriaId: number, value: string) => {
    setComments(prev => ({ ...prev, [criteriaId]: value }));
  };

  const handleSubmit = () => {
    if (!allScored) return;
    props.onSubmit(scores, comments);
  };

  return (
    <div className="RubricForm">
      {props.criteria.map((criterion) => (
        <div key={criterion.id} className="RubricForm-criterion">
          <div className="RubricForm-question">{criterion.question}</div>

          {criterion.has_score && (
            <ScoreInput
              value={scores[criterion.id] ?? null}
              maxScore={criterion.score_max}
              onChange={(value) => handleScoreChange(criterion.id, value)}
            />
          )}

          {criterion.can_comment && (
            <textarea
              className="RubricForm-comment"
              placeholder="Add a comment (optional)"
              value={comments[criterion.id] || ''}
              onChange={(e) => handleCommentChange(criterion.id, e.target.value)}
            />
          )}
        </div>
      ))}

      <div className="RubricForm-actions">
        <Button
          onClick={handleSubmit}
          disabled={!allScored || props.disabled}
        >
          Submit Review
        </Button>
        {!allScored && (
          <p className="RubricForm-hint">Please score all criteria before submitting.</p>
        )}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react';
import { getRubricByAssignment } from '../util/api';
import './RubricDisplay.css';

interface RubricCriterion {
  id: number;
  title: string;
  question?: string;
  description: string;
  score_max?: number;
  scoreMax?: number;
  levels: RubricLevel[];
}

interface RubricLevel {
  id: number;
  score: number;
  description: string;
}

interface RubricResponse {
  id: number;
  title: string;
  criteria: RubricCriterion[];
}

interface RubricDisplayProps {
  rubricId: number;
}

export default function RubricDisplay({ rubricId }: RubricDisplayProps) {
  const [rubric, setRubric] = useState<RubricResponse | null>(null);

  useEffect(() => {
    if (!rubricId) return;
    getRubricByAssignment(rubricId)
      .then((data) => setRubric(data as RubricResponse))
      .catch(() => setRubric(null));
  }, [rubricId]);

  if (!rubric || rubric.criteria.length === 0) {
    return (
      <div className="RubricDisplay">
        <p className="RubricDisplay__empty">No rubric assigned yet.</p>
      </div>
    );
  }

  return (
    <div className="RubricDisplay">
      <h3 className="RubricDisplay__title">{rubric.title}</h3>
      <table className="RubricDisplay__table">
        <tbody>
          {rubric.criteria.map((criterion) => (
            <tr key={criterion.id}>
              <td className="RubricDisplay__criterion-title">
                {criterion.title || criterion.question}
              </td>
              {criterion.levels ? criterion.levels.map((level) => (
                <td key={level.id} className="RubricDisplay__level">
                  <div className="RubricDisplay__level-score">{level.score}</div>
                  <div className="RubricDisplay__level-desc">{level.description}</div>
                </td>
              )) : (
                <td className="RubricDisplay__level">
                  <div className="RubricDisplay__level-score">
                    {criterion.score_max || criterion.scoreMax}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
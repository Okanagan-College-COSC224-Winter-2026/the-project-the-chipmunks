import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, ResponsiveContainer, Cell,
} from 'recharts';
import { CriterionStat } from '../util/api';
import './CriterionBarChart.css';

interface Props {
  criteria: CriterionStat[];
}

export default function CriterionBarChart({ criteria }: Props) {
  if (criteria.length === 0) {
    return (
      <div className="CriterionBarChart">
        <h3>Average Score by Criterion</h3>
        <p className="CriterionBarChart__empty">No rubric criteria found.</p>
      </div>
    );
  }

  const data = criteria.map((c) => ({
    name:    c.criterion_name,
    average: c.avg_score,
    max:     c.score_max,
    count:   c.response_count,
  }));

  return (
    <div className="CriterionBarChart">
      <h3>Average Score by Criterion</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 70 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-35}
            textAnchor="end"
            interval={0}
            tick={{ fontSize: 12 }}
          />
          <YAxis domain={[0, 'dataMax']} />
          <Tooltip
            formatter={(value: number, _name: string, props: { payload: { max: number } }) => [
              `${value.toFixed(2)} / ${props.payload.max}`,
              'Avg Score',
            ]}
          />
          <Bar dataKey="average" name="Avg Score" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill="#E10054" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

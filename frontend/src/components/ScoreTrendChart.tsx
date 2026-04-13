import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface TrendPoint {
  assignment_name: string;
  my_avg: number;
  review_count: number;
}

export default function ScoreTrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic', fontSize: '0.9rem' }}>No review data yet.</p>;
  }

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#D9C6B2" />
          <XAxis dataKey="assignment_name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 'auto']} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="my_avg"
            stroke="#B22234"
            strokeWidth={2}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
            name="My Average"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
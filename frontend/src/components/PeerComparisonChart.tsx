import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface ComparisonPoint {
  assignment_name: string;
  my_avg: number;
  class_avg: number;
}

export default function PeerComparisonChart({ data }: { data: ComparisonPoint[] }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic', fontSize: '0.9rem' }}>No comparison data yet.</p>;
  }

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#D9C6B2" />
          <XAxis dataKey="assignment_name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 'auto']} />
          <Tooltip />
          <Legend />
          <Bar dataKey="my_avg" fill="#B22234" name="My Score" radius={[4, 4, 0, 0]} />
          <Bar dataKey="class_avg" fill="#D9C6B2" name="Class Average" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
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
    return <p style={{ color: '#718096' }}>No comparison data yet.</p>;
  }

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="assignment_name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 'auto']} />
          <Tooltip />
          <Legend />
          <Bar dataKey="my_avg" fill="#2B6CB0" name="My Score" radius={[4, 4, 0, 0]} />
          <Bar dataKey="class_avg" fill="#A0AEC0" name="Class Average" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
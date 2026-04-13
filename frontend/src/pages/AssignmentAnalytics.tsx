import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getAssignmentAnalytics,
  exportReviewsCSV,
  AnalyticsData,
} from '../util/api';
import ExportReportButton from '../components/ExportReportButton';
import CriterionBarChart from '../components/CriterionBarChart';
import CompletionRing from '../components/CompletionRing';
import OutlierTable from '../components/OutlierTable';
import './AssignmentAnalytics.css';

export default function AssignmentAnalytics() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!id) return;
    getAssignmentAnalytics(Number(id))
      .then((res) => {
        if (!res || !res.ok) throw new Error('Failed to load');
        return res.json();
      })
      .then(setData)
      .catch(() => setError('Failed to load analytics.'))
      .finally(() => setLoading(false));
  }, [id]);

  const downloadCSV = async () => {
    setExporting(true);
    try {
      const res = await exportReviewsCSV(Number(id));
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `assignment_${id}_reviews.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      alert('CSV export failed.');
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <div className="AssignmentAnalytics"><p>Loading analytics...</p></div>;
  if (error)   return <div className="AssignmentAnalytics"><p className="AssignmentAnalytics__error">{error}</p></div>;
  if (!data)   return null;

  return (
    <div className="AssignmentAnalytics">
      <div className="AssignmentAnalytics__header">
        <div>
          <h1>Analytics</h1>
          <p className="AssignmentAnalytics__subtitle">{data.assignment_name}</p>
        </div>
        <div className="AssignmentAnalytics__headerActions">
  <button
    className="AssignmentAnalytics__csvBtn"
    onClick={downloadCSV}
    disabled={exporting}
  >
    {exporting ? 'Exporting...' : '⬇ Download CSV'}
  </button>
  <ExportReportButton
    assignmentId={Number(id)}
    assignmentTitle={data.assignment_name}
  />
  <button
    className="AssignmentAnalytics__backBtn"
    onClick={() => navigate(-1)}
  >
    ← Back to Reviews
  </button>
</div>
      </div>

      {/* Summary row */}
      <div className="AssignmentAnalytics__summary">
        <CompletionRing
          pct={data.completion_pct}
          submitted={data.submitted}
          total={data.total_students}
        />
        <CriterionBarChart criteria={data.criteria} />
      </div>

      {/* Criteria stats table */}
      {data.criteria.length > 0 && (
        <div className="AssignmentAnalytics__criteriaWrap">
          <h3>Criterion Breakdown</h3>
          <table className="AssignmentAnalytics__criteriaTable">
            <thead>
              <tr>
                <th>Criterion</th>
                <th>Avg Score</th>
                <th>Max Score</th>
                <th>Responses</th>
              </tr>
            </thead>
            <tbody>
              {data.criteria.map((c) => (
                <tr key={c.criterion_id}>
                  <td>{c.criterion_name}</td>
                  <td>{c.avg_score.toFixed(2)}</td>
                  <td>{c.score_max}</td>
                  <td>{c.response_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <OutlierTable outliers={data.outliers} />
    </div>
  );
}

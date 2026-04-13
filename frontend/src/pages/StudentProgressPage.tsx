import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getCourseProgress } from '../util/api';
import StatusMessage from '../components/StatusMessage';
import './StudentProgressPage.css';

interface ProgressPerAssignment {
  in_group: boolean;
  reviews_given: number;
  reviews_received: number;
  avg_score: number | null;
}

interface ProgressStudent {
  user_id: number;
  name: string;
  email: string;
  per_assignment: Record<string, ProgressPerAssignment>;
}

interface CourseProgressResponse {
  course_id: number;
  course_name: string;
  assignments: { id: number; name: string }[];
  students: ProgressStudent[];
}

export default function StudentProgressPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const [data, setData] = useState<CourseProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!courseId) return;
    getCourseProgress(Number(courseId))
      .then((res) => {
        if (!res.ok) {
          return res.json().then((body) => {
            throw new Error(body?.msg || `Error ${res.status}`);
          });
        }
        return res.json();
      })
      .then((json: CourseProgressResponse) => {
        setData(json);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message || 'Failed to load progress data.');
        setLoading(false);
      });
  }, [courseId]);

  if (loading) return <StatusMessage type="success" message="Loading student progress..." />;
  if (error)   return <StatusMessage type="error"   message={error} />;
  if (!data)   return null;

  // ── Filtered student rows ─────────────────────────────────────────────────
  const q = search.trim().toLowerCase();
  const filtered = data.students.filter(
    (s) =>
      s.name.toLowerCase().includes(q) ||
      s.email.toLowerCase().includes(q)
  );

  // ── Completion badge ──────────────────────────────────────────────────────
  // % of students who gave at least 1 review across any assignment
  const completedCount = data.students.filter((s) =>
    data.assignments.some(
      (a) => (s.per_assignment[String(a.id)]?.reviews_given ?? 0) > 0
    )
  ).length;
  const completionPct =
    data.students.length > 0
      ? Math.round((completedCount / data.students.length) * 100)
      : 0;

  return (
    <div className="progress-page">
      <div className="progress-header">
        <div className="progress-header-left">
          <h1 className="progress-title">Student Progress</h1>
          <span className="progress-course-name">{data.course_name}</span>
        </div>
        <div className="progress-badge-wrap">
          <div
            className="progress-badge"
            title={`${completedCount} of ${data.students.length} students have submitted at least one review`}
          >
            <span className="progress-badge-pct">{completionPct}%</span>
            <span className="progress-badge-label">Submitted</span>
          </div>
        </div>
      </div>

      <div className="progress-controls">
        <input
          className="progress-search"
          type="text"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="progress-count">
          {filtered.length} student{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="progress-table-wrap">
        {data.assignments.length === 0 ? (
          <p className="progress-empty">No assignments in this course yet.</p>
        ) : (
          <table className="progress-table">
            <thead>
              <tr>
                <th className="progress-th progress-th-student">Student</th>
                {data.assignments.map((a) => (
                  <th key={a.id} className="progress-th progress-th-assignment">
                    {a.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={data.assignments.length + 1}
                    className="progress-no-results"
                  >
                    No students match your search.
                  </td>
                </tr>
              ) : (
                filtered.map((student) => (
                  <tr key={student.user_id} className="progress-row">
                    <td className="progress-td progress-td-student">
                      <span className="progress-student-name">{student.name}</span>
                      <span className="progress-student-email">{student.email}</span>
                    </td>
                    {data.assignments.map((a) => {
                      const cell = student.per_assignment[String(a.id)];
                      if (!cell) {
                        return (
                          <td key={a.id} className="progress-td progress-td-cell progress-td-missing">
                            —
                          </td>
                        );
                      }
                      return (
                        <td key={a.id} className="progress-td progress-td-cell">
                          <div className="progress-cell">
                            <span
                              className={`progress-group-badge ${
                                cell.in_group
                                  ? 'progress-group-badge--in'
                                  : 'progress-group-badge--out'
                              }`}
                              title={cell.in_group ? 'In a group' : 'Not in a group'}
                            >
                              {cell.in_group ? '✓ Grouped' : '✗ No group'}
                            </span>
                            <div className="progress-stats">
                              <span
                                className="progress-stat"
                                title="Reviews given"
                              >
                                ↑ {cell.reviews_given}
                              </span>
                              <span
                                className="progress-stat"
                                title="Reviews received"
                              >
                                ↓ {cell.reviews_received}
                              </span>
                              <span
                                className="progress-stat progress-stat-score"
                                title="Average score received"
                              >
                                {cell.avg_score !== null
                                  ? `★ ${cell.avg_score.toFixed(1)}`
                                  : '★ —'}
                              </span>
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

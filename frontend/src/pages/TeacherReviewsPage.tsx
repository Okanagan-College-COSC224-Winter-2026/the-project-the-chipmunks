import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Button from "../components/Button";
import ReviewDetailModal from "../components/ReviewDetailModal";
import StatusMessage from "../components/StatusMessage";
import { isTeacher } from "../util/login";
import {
  teacherListReviews,
  getAssignment,
  listCourseMembers,
  listAllGroups,
  getAssignmentCompletion,
  type TeacherReviewRow,
} from "../util/api";
import "./TeacherReviewsPage.css";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ReviewedEntry {
  reviewee_id: number;
  reviewee_name: string;
}

interface CompletionStudent {
  user_id: number;
  name: string;
  status: "Complete" | "Incomplete";
  reviews_given: number;
  reviewed: ReviewedEntry[];
}

interface CompletionData {
  assignment_id: number;
  assignment_name: string;
  total: number;
  submitted: number;
  completion_pct: number;
  students: CompletionStudent[];
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function TeacherReviewsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const assignmentId = Number(id);

  // Reviews tab state
  const [reviews, setReviews] = useState<TeacherReviewRow[]>([]);
  const [sort, setSort] = useState("id");
  const [groupId, setGroupId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);
  const [memberNames, setMemberNames] = useState<Record<number, string>>({});
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);

  // Completion tab state
  const [activeTab, setActiveTab] = useState<"reviews" | "completion">("reviews");
  const [completion, setCompletion] = useState<CompletionData | null>(null);
  const [completionLoading, setCompletionLoading] = useState(false);

  // Load member names + groups once on mount
  useEffect(() => {
    (async () => {
      try {
        const assignment = await getAssignment(assignmentId);
        if (assignment.courseID) {
          const members = await listCourseMembers(String(assignment.courseID));
          const nameMap: Record<number, string> = {};
          members.forEach((m: { id: number; name: string }) => {
            nameMap[m.id] = m.name;
          });
          setMemberNames(nameMap);
        }
        const groupData = await listAllGroups(assignmentId).catch(() => []);
        setGroups(groupData);
      } catch {
        // Names unavailable — fall back to IDs
      }
    })();
  }, [assignmentId]);

  // Load reviews when filters change
  useEffect(() => {
    if (Number.isNaN(assignmentId) || assignmentId <= 0) return;
    const load = async () => {
      try {
        setLoading(true);
        setError("");
        const data = await teacherListReviews(assignmentId, groupId, sort);
        setReviews(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load reviews");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [assignmentId, groupId, sort]);

  // Load completion data lazily when that tab is first opened
  useEffect(() => {
    if (activeTab !== "completion" || completion !== null) return;
    const load = async () => {
      setCompletionLoading(true);
      try {
        const data = await getAssignmentCompletion(assignmentId);
        setCompletion(data);
      } catch {
        // fail silently
      } finally {
        setCompletionLoading(false);
      }
    };
    load();
  }, [activeTab, assignmentId, completion]);

  const nameOf = (userId: number) => memberNames[userId] || `#${userId}`;

  if (!isTeacher()) {
    return (
      <div className="TeacherReviewsPage">
        <h1>Submitted Reviews</h1>
        <StatusMessage message="Access denied." type="error" />
      </div>
    );
  }

  return (
    <div className="TeacherReviewsPage">
      {/* Header */}
      <div className="TeacherReviewsPage__header">
        <div>
          <h1>Submitted Reviews</h1>
          <p>Assignment #{assignmentId}</p>
        </div>
        <Button onClick={() => navigate(`/assignments/${assignmentId}/analytics`)}>
          View Analytics
        </Button>
      </div>

      {/* Tab switcher */}
      <div className="TeacherReviewsPage__tabs">
        <button
          className={`TeacherReviewsPage__tab ${activeTab === "reviews" ? "TeacherReviewsPage__tab--active" : ""}`}
          onClick={() => setActiveTab("reviews")}
        >
          Reviews
        </button>
        <button
          className={`TeacherReviewsPage__tab ${activeTab === "completion" ? "TeacherReviewsPage__tab--active" : ""}`}
          onClick={() => setActiveTab("completion")}
        >
          Completion Status
        </button>
      </div>

      {/* ── Reviews tab ──────────────────────────────────────────────────── */}
      {activeTab === "reviews" && (
        <div>
          <div className="TeacherReviewsPage__filters">
            <label>
              Sort
              <select value={sort} onChange={(e) => setSort(e.target.value)}>
                <option value="id">Sort by ID</option>
                <option value="score">Sort by Score</option>
              </select>
            </label>

            <label>
              Group
              <select value={groupId} onChange={(e) => setGroupId(e.target.value)}>
                <option value="">All groups</option>
                {groups.map((g) => (
                  <option key={g.id} value={String(g.id)}>
                    {g.name || `Group ${g.id}`}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {loading && <p>Loading...</p>}
          {error && <StatusMessage message={error} type="error" />}

          {!loading && !error && (
            <div className="TeacherReviews__tableWrap">
              <table className="TeacherReviews__table">
                <thead>
                  <tr>
                    <th>Review ID</th>
                    <th>Reviewer</th>
                    <th>Reviewee</th>
                    <th>Total Score</th>
                    <th>Note?</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reviews.length === 0 && (
                    <tr>
                      <td colSpan={6}>No reviews found.</td>
                    </tr>
                  )}
                  {reviews.map((review) => (
                    <tr key={review.review_id}>
                      <td>{review.review_id}</td>
                      <td>{nameOf(review.reviewer_id)}</td>
                      <td>{nameOf(review.reviewee_id)}</td>
                      <td>{review.total_score}</td>
                      <td>{review.has_conclusion ? "✓" : "—"}</td>
                      <td>
                        <Button onClick={() => setSelectedReviewId(review.review_id)}>
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Completion tab ───────────────────────────────────────────────── */}
      {activeTab === "completion" && (
        <div className="TeacherReviewsPage__completion">
          {completionLoading && <p>Loading...</p>}

          {!completionLoading && completion && (
            <>
              <div className="completion-summary">
                <span className="completion-pct">{completion.completion_pct}%</span>
                <span className="completion-label">
                  {completion.submitted} of {completion.total} students submitted
                </span>
              </div>

              <div className="TeacherReviews__tableWrap">
                <table className="TeacherReviews__table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Status</th>
                      <th>Reviews Given</th>
                      <th>Reviewed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completion.students.length === 0 && (
                      <tr>
                        <td colSpan={4}>No students found.</td>
                      </tr>
                    )}
                    {completion.students.map((s) => (
                      <tr
                        key={s.user_id}
                        className={s.status === "Incomplete" ? "completion-row--incomplete" : ""}
                      >
                        <td>{s.name}</td>
                        <td>
                          <span className={`completion-badge completion-badge--${s.status.toLowerCase()}`}>
                            {s.status}
                          </span>
                        </td>
                        <td>{s.reviews_given}</td>
                        <td>
                          {s.reviewed.length === 0
                            ? "—"
                            : s.reviewed.map((r) => r.reviewee_name).join(", ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Review detail modal */}
      {selectedReviewId !== null && (
        <ReviewDetailModal
          assignmentId={assignmentId}
          reviewId={selectedReviewId}
          memberNames={memberNames}
          onClose={() => setSelectedReviewId(null)}
        />
      )}
    </div>
  );
}

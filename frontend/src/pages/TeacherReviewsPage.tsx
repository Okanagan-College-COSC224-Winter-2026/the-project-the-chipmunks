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
  type TeacherReviewRow,
} from "../util/api";
import "./TeacherReviewsPage.css";

export default function TeacherReviewsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const assignmentId = Number(id);

  const [reviews, setReviews] = useState<TeacherReviewRow[]>([]);
  const [sort, setSort] = useState("id");
  const [groupId, setGroupId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);
  const [memberNames, setMemberNames] = useState<Record<number, string>>({});
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);

  // Load member names once on mount
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
        // Load groups for dropdown filter
        const groupData = await listAllGroups(assignmentId).catch(() => []);
        setGroups(groupData);
      } catch {
        // Names unavailable — fall back to IDs
      }
    })();
  }, [assignmentId]);

  useEffect(() => {
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

    if (!Number.isNaN(assignmentId) && assignmentId > 0) {
      load();
    }
  }, [assignmentId, groupId, sort]);

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
      <div className="TeacherReviewsPage__header">
        <div>
          <h1>Submitted Reviews</h1>
          <p>Assignment #{assignmentId}</p>
        </div>
        <Button onClick={() => navigate(`/assignments/${assignmentId}/analytics`)}>
          View Analytics
        </Button>
      </div>

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

      {selectedReviewId !== null && (
        <ReviewDetailModal
          assignmentId={assignmentId}
          reviewId={selectedReviewId}
          onClose={() => setSelectedReviewId(null)}
        />
      )}
    </div>
  );
}
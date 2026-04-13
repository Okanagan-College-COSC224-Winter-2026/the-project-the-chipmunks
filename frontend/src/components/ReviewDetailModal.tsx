import { useEffect, useState } from "react";
import Button from "./Button";
import ConclusionForm from "./ConclusionForm";
import StatusMessage from "./StatusMessage";
import {
  teacherGetReviewDetail,
  type TeacherReviewDetail,
} from "../util/api";

interface Props {
  assignmentId: number;
  reviewId: number;
  memberNames: Record<number, string>;
  onClose: () => void;
}

export default function ReviewDetailModal({
  assignmentId,
  reviewId,
  memberNames,
  onClose,
}: Props) {
  const nameOf = (id: number) => memberNames[id] || `#${id}`;
  const [detail, setDetail] = useState<TeacherReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError("");
        const data = await teacherGetReviewDetail(assignmentId, reviewId);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load review");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [assignmentId, reviewId]);

  return (
    <div className="TeacherReviews__modalOverlay" onClick={onClose}>
      <div
        className="TeacherReviews__modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="TeacherReviews__modalHeader">
          <div>
            <h2>Review #{reviewId}</h2>
            {detail && (
              <p>
                {nameOf(detail.reviewer_id)} → {nameOf(detail.reviewee_id)}
              </p>
            )}
          </div>

          <Button onClick={onClose} type="secondary">
            Close
          </Button>
        </div>

        {loading && <p>Loading...</p>}
        {error && <StatusMessage message={error} type="error" />}

        {detail && (
          <>
            <div className="TeacherReviews__tableWrap">
              <table className="TeacherReviews__table">
                <thead>
                  <tr>
                    <th>Criterion</th>
                    <th>Score</th>
                    <th>Max</th>
                    <th>Comment</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.criteria.map((criterion, index) => (
                    <tr key={`${criterion.criterion_id}-${index}`}>
                      <td>{criterion.criterion_name}</td>
                      <td>{criterion.score ?? "—"}</td>
                      <td>{criterion.score_max ?? "—"}</td>
                      <td>{criterion.comment || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ConclusionForm
              reviewId={detail.review_id}
              existingNote={detail.conclusion?.note}
              onSaved={(note) =>
                setDetail({
                  ...detail,
                  conclusion: {
                    ...(detail.conclusion || {}),
                    note,
                  },
                })
              }
            />
          </>
        )}
      </div>
    </div>
  );
}
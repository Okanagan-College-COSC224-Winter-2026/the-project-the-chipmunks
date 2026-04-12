import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import RubricForm from '../components/RubricForm'
import StatusMessage from '../components/StatusMessage'
import { getRubricByAssignment, submitReview, uploadReviewFiles } from '../util/api'
import './ReviewSubmission.css'
import ReviewFileUpload from '../components/ReviewFileUpload'

export default function ReviewSubmission() {
  const { id, revieweeId } = useParams();
  const [rubric, setRubric] = useState<RubricResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const data = await getRubricByAssignment(Number(id));
        setRubric(data);
      } catch (err) {
        console.error(err);
        setError('Failed to load rubric. Please try again.');
      }

      setLoading(false);
    })();
  }, [id, revieweeId]);

  const handleSubmit = async (scores: Record<number, number>, comments: Record<number, string>) => {
    if (!rubric) return;

    setError('');
    setSuccess('');
    setSubmitting(true);

    const criteria: CriterionSubmission[] = rubric.criteria.map((c) => ({
      criteria_description_id: c.id,
      grade: scores[c.id] ?? 0,
      comments: comments[c.id] || '',
    }));

    try {
      const data = await submitReview({
        assignment_id: Number(id),
        reviewee_id: Number(revieweeId),
        criteria,
      });

      if (attachedFiles.length > 0) {
        await uploadReviewFiles(data.review_id, attachedFiles);
      }

      setSuccess('Review submitted successfully!');
      setTimeout(() => {
        window.location.href = `/assignments/${id}`;
      }, 2000);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to submit review. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="ReviewSubmission">
        <p>Loading rubric...</p>
      </div>
    );
  }

  return (
    <div className="ReviewSubmission">
      <div className="ReviewSubmission-header">
        <h2>Peer Review</h2>
        <p className="ReviewSubmission-subtitle">
          Reviewing: <strong>Anonymous Peer</strong>
        </p>
      </div>

      <StatusMessage message={error} type="error" />
      <StatusMessage message={success} type="success" />

      {rubric && rubric.criteria.length > 0 ? (
        <>
          <ReviewFileUpload files={attachedFiles} onChange={setAttachedFiles} />
          <RubricForm
            criteria={rubric.criteria}
            onSubmit={handleSubmit}
            disabled={submitting}
          />
        </>
      ) : (
        <p>No rubric criteria available for this assignment.</p>
      )}
    </div>
  );
}

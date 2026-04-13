import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import FeedbackCard from "../components/FeedbackCard"
import { getStudentFeedback } from "../util/api"
import './FeedbackView.css'

export default function FeedbackView() {
  const { id } = useParams()
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ; (async () => {
      try {
        const data = await getStudentFeedback(Number(id))
        setFeedback(data)
      } catch (err) {
        console.error("Error fetching feedback:", err)
        setError("Failed to load feedback. Please try again later.")
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  if (loading) {
    return (
      <div className="FeedbackView">
        <h1>Your Feedback</h1>
        <p>Loading feedback...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="FeedbackView">
        <h1>Your Feedback</h1>
        <div className="FeedbackView__error">
          <p>{error}</p>
        </div>
      </div>
    )
  }

  // Empty state — no reviews submitted yet
  if (!feedback || feedback.total_reviews === 0) {
    return (
      <div className="FeedbackView">
        <h1>Your Feedback</h1>
        <div className="FeedbackView__empty">
          <h2>No feedback available yet</h2>
          <p>Your peers haven't submitted reviews for this assignment yet. Check back later.</p>
        </div>
      </div>
    )
  }

  // Calculate overall percentage for the summary
  const criteria = feedback.criteria_feedback ?? [];
  const overallMaxPossible = criteria.length > 0
    ? criteria.reduce((sum, c) => sum + c.score_max, 0) / criteria.length
    : 0
  const overallPercentage = overallMaxPossible > 0
    ? (feedback.overall_avg / overallMaxPossible) * 100
    : 0
  const overallColor = overallPercentage >= 75 ? "green" : overallPercentage >= 50 ? "yellow" : "red"

  return (
    <div className="FeedbackView">
      <h1>{feedback.assignment_name}</h1>
      <h2>Your Feedback</h2>

      {/* Summary card */}
      <div className="FeedbackView__summary">
        <div className="FeedbackView__summaryItem">
          <span className="FeedbackView__summaryLabel">Overall Average</span>
          <span className={`FeedbackView__summaryValue FeedbackView__summaryValue--${overallColor}`}>
            {feedback.overall_avg.toFixed(1)}
          </span>
        </div>
        <div className="FeedbackView__summaryItem">
          <span className="FeedbackView__summaryLabel">Reviewers</span>
          <span className="FeedbackView__summaryValue">
            {feedback.total_reviews}
          </span>
        </div>
      </div>

      {/* Criterion feedback cards */}
      <div className="FeedbackView__cards">
        {criteria.map((criterion, index) => (
          <FeedbackCard
            key={index}
            question={criterion.question}
            avgScore={criterion.avg_score}
            maxScore={criterion.score_max}
            comments={criterion.comments}
          />
        ))}
      </div>
    </div>
  )
}
import { useEffect, useState } from 'react';
import PeerComparisonChart, { type ComparisonPoint } from '../components/PeerComparisonChart';
import ScoreTrendChart, { type TrendPoint } from '../components/ScoreTrendChart';
import { getMyReviews, getMyTrends } from '../util/api';
import './ReviewHistoryPage.css';

interface ReviewItem {
  id: number;
  assignment_name: string;
  other_student: string;
  score: number | null;
  role: string;
  created_at: string | null;
}

interface ReviewsResponse {
  given: ReviewItem[];
  received: ReviewItem[];
}

interface TrendsResponse {
  trend: TrendPoint[];
  comparison: ComparisonPoint[];
}

export default function ReviewHistoryPage() {
  const [given, setGiven] = useState<ReviewItem[]>([]);
  const [received, setReceived] = useState<ReviewItem[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [comparison, setComparison] = useState<ComparisonPoint[]>([]);
  const [tab, setTab] = useState<'received' | 'given'>('received');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [reviewsResp, trendsResp] = await Promise.all([getMyReviews(), getMyTrends()]);

        if (reviewsResp.ok) {
          const reviewsData = (await reviewsResp.json()) as ReviewsResponse;
          setGiven(reviewsData.given ?? []);
          setReceived(reviewsData.received ?? []);
        }

        if (trendsResp.ok) {
          const trendsData = (await trendsResp.json()) as TrendsResponse;
          setTrend(trendsData.trend ?? []);
          setComparison(trendsData.comparison ?? []);
        }
      } catch (error) {
        console.error('Failed to load review history:', error);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return <p>Loading review history...</p>;
  }

  const reviews = tab === 'received' ? received : given;

  return (
    <div className="review-history-page">
      <h1>My Review History</h1>

      <section className="rh-section">
        <h2>Score Trend</h2>
        <ScoreTrendChart data={trend} />
      </section>

      <section className="rh-section">
        <h2>My Score vs Class Average</h2>
        <PeerComparisonChart data={comparison} />
      </section>

      <section className="rh-section">
        <h2>Reviews</h2>

        <div className="rh-tabs">
          <button
            className={tab === 'received' ? 'active' : ''}
            onClick={() => setTab('received')}
          >
            Received ({received.length})
          </button>
          <button
            className={tab === 'given' ? 'active' : ''}
            onClick={() => setTab('given')}
          >
            Given ({given.length})
          </button>
        </div>

        <div className="rh-review-list">
          {reviews.map((review) => (
            <div key={review.id} className="rh-review-item">
              <div className="rh-review-main">
                <p className="rh-assignment">{review.assignment_name}</p>
                <p className="rh-student">
                  {tab === 'received'
                    ? <span className="rh-anonymous">From: Anonymous Peer</span>
                    : `To: ${review.other_student}`}
                </p>
              </div>

              <div className="rh-review-meta">
                {review.score !== null && <span className="rh-score">{review.score}</span>}
                {review.created_at && (
                  <span className="rh-date">
                    {new Date(review.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}

          {reviews.length === 0 && <p className="rh-empty">No reviews to show.</p>}
        </div>
      </section>
    </div>
  );
}
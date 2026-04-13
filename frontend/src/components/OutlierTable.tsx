import './OutlierTable.css';

interface Outlier {
  review_id: number;
  reviewer_id: number;
  reviewee_id: number;
  total_score: number;
  deviation: number;
}

interface Props {
  outliers: Outlier[];
}

export default function OutlierTable({ outliers }: Props) {
  if (outliers.length === 0) {
    return (
      <div className="OutlierTable">
        <h3>Flagged Outlier Reviews (&gt;2σ from mean)</h3>
        <p className="OutlierTable__empty">No outlier reviews detected.</p>
      </div>
    );
  }

  return (
    <div className="OutlierTable">
      <h3>Flagged Outlier Reviews (&gt;2σ from mean)</h3>
      <div className="OutlierTable__wrap">
        <table className="OutlierTable__table">
          <thead>
            <tr>
              <th>Review ID</th>
              <th>Reviewer</th>
              <th>Reviewee</th>
              <th>Total Score</th>
              <th>Deviation</th>
            </tr>
          </thead>
          <tbody>
            {outliers.map((o) => (
              <tr
                key={o.review_id}
                className={o.deviation < 0 ? 'OutlierTable__row--low' : 'OutlierTable__row--high'}
              >
                <td>{o.review_id}</td>
                <td>#{o.reviewer_id}</td>
                <td>#{o.reviewee_id}</td>
                <td>{o.total_score}</td>
                <td className={o.deviation < 0 ? 'OutlierTable__neg' : 'OutlierTable__pos'}>
                  {o.deviation > 0 ? '+' : ''}{o.deviation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

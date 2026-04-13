import ScoreBar from './ScoreBar'
import CommentList from './CommentList'
import './FeedbackCard.css'

interface Props {
  question: string;
  avgScore: number;
  maxScore: number;
  comments: string[];
}

export default function FeedbackCard(props: Props) {
  return (
    <div className="FeedbackCard">
      <h3 className="FeedbackCard__question">{props.question}</h3>
      <div className="FeedbackCard__score">
        <ScoreBar avgScore={props.avgScore} maxScore={props.maxScore} />
      </div>
      <div className="FeedbackCard__comments">
        <CommentList comments={props.comments} />
      </div>
    </div>
  )
}

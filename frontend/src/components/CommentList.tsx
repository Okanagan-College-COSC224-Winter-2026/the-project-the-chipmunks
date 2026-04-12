import './CommentList.css'

interface Props {
  comments: string[];
}

export default function CommentList(props: Props) {
  // Filter out empty comments
  const validComments = props.comments.filter((c) => c.trim().length > 0)

  if (validComments.length === 0) {
    return (
      <div className="CommentList CommentList--empty">
        <p>No comments for this criterion.</p>
      </div>
    )
  }

  return (
    <div className="CommentList">
      {validComments.map((comment, index) => (
        <div key={index} className="CommentList__item">
          <span className="CommentList__icon">💬</span>
          <p>{comment}</p>
        </div>
      ))}
    </div>
  )
}

import AvatarInitials from './AvatarInitials';
import './AnnouncementCard.css';

interface Props {
  id: number;
  title: string;
  content: string;
  author_name: string;
  created_at: string;
  canDelete: boolean;
  onDelete: (id: number) => void;
}

export default function AnnouncementCard({
  id,
  title,
  content,
  author_name,
  created_at,
  canDelete,
  onDelete,
}: Props) {
  const [firstName = '', lastName = ''] = author_name.split(' ');

  return (
    <div className="announcement-card">
      <div className="announcement-header">
        <AvatarInitials firstName={firstName} lastName={lastName} size={32} />
        <div className="announcement-meta">
          <span className="announcement-author">{author_name}</span>
          <span className="announcement-date">
            {new Date(created_at).toLocaleDateString()}
          </span>
        </div>
        {canDelete && (
          <button
            className="announcement-delete"
            onClick={() => onDelete(id)}
            title="Delete announcement"
          >
            ✕
          </button>
        )}
      </div>
      <h3 className="announcement-title">{title}</h3>
      <p className="announcement-content">{content}</p>
    </div>
  );
}

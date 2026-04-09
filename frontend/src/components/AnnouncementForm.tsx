import { useState } from 'react';
import './AnnouncementForm.css';

interface Props {
  onSubmit: (title: string, content: string) => Promise<void>;
}

export default function AnnouncementForm({ onSubmit }: Props) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [posting, setPosting] = useState(false);

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) return;
    setPosting(true);
    await onSubmit(title.trim(), content.trim());
    setTitle('');
    setContent('');
    setPosting(false);
  };

  return (
    <div className="announcement-form">
      <h3>Post Announcement</h3>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Announcement title..."
        maxLength={200}
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Write your announcement..."
        rows={3}
      />
      <button
        onClick={handleSubmit}
        disabled={posting || !title.trim() || !content.trim()}
      >
        {posting ? 'Posting...' : 'Post Announcement'}
      </button>
    </div>
  );
}

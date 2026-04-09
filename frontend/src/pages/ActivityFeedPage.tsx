import { useEffect, useState } from 'react';
import { useNotifications, Notification } from '../hooks/useNotifications';
import './ActivityFeedPage.css';

const TYPE_LABELS: Record<string, string> = {
  review_assigned: 'Reviews Assigned',
  review_received: 'Reviews Received',
  grade_posted: 'Grades',
  feedback_received: 'Feedback',
  account_update: 'Account',
  announcement: 'Announcements',
};

const TYPE_ICONS: Record<string, string> = {
  review_assigned: '\u{1F4DD}',
  review_received: '\u2B50',
  grade_posted: '\u{1F3C6}',
  feedback_received: '\u{1F4AC}',
  account_update: '\u{1F512}',
  announcement: '\u{1F4E2}',
};

export default function ActivityFeedPage() {
  const { notifications, loading, page, totalPages, fetchNotifications, markRead, loadMore } = useNotifications();
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);

  useEffect(() => { fetchNotifications(1, typeFilter); }, [typeFilter, fetchNotifications]);

  const handleClick = (n: Notification) => {
    if (!n.is_read) markRead(n.id);
    if (n.link) window.location.href = n.link;
  };

  return (
    <div className="activity-feed-page">
      <h1>Activity Feed</h1>
      <div className="activity-filters">
        <button className={!typeFilter ? 'active' : ''} onClick={() => setTypeFilter(undefined)}>All</button>
        {Object.entries(TYPE_LABELS).map(([key, label]) => (
          <button key={key} className={typeFilter === key ? 'active' : ''} onClick={() => setTypeFilter(key)}>{label}</button>
        ))}
      </div>
      <div className="activity-list">
        {notifications.map(n => (
          <div key={n.id} className={`activity-item ${!n.is_read ? 'unread' : ''}`} onClick={() => handleClick(n)}>
            <span className="activity-icon">{TYPE_ICONS[n.type] || '\u{1F514}'}</span>
            <div className="activity-main">
              <p className="activity-title">{n.title}</p>
              <p className="activity-message">{n.message}</p>
            </div>
            <span className="activity-time">{new Date(n.created_at).toLocaleString()}</span>
          </div>
        ))}
        {notifications.length === 0 && !loading && <p className="activity-empty">No activity to show.</p>}
      </div>
      {page < totalPages && (
        <button className="activity-load-more" onClick={loadMore} disabled={loading}>
          {loading ? 'Loading...' : 'Load more'}
        </button>
      )}
    </div>
  );
}

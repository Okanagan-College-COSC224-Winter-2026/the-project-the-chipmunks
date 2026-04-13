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

const TYPE_ICONS: Record<string, JSX.Element> = {
  review_assigned: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>
  ),
  review_received: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  grade_posted: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="6"/>
      <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>
    </svg>
  ),
  feedback_received: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  account_update: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
  ),
  announcement: (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  ),
};

const BellIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
);

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
            <span className="activity-icon">{TYPE_ICONS[n.type] || <BellIcon />}</span>
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

import { useState, useRef, useEffect } from 'react';
import { useNotifications, Notification } from '../hooks/useNotifications';
import './NotificationBell.css';

export default function NotificationBell() {
  const {
    unreadCount,
    notifications,
    fetchNotifications,
    markRead,
    markAllRead,
  } = useNotifications();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) fetchNotifications(1);
  }, [open, fetchNotifications]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleClick = (n: Notification) => {
    if (!n.is_read) markRead(n.id);
    if (n.link) window.location.href = n.link;
    setOpen(false);
  };

  const typeIcon: Record<string, string> = {
    review_assigned: '\u{1F4DD}',
    review_received: '\u2B50',
    grade_posted: '\u{1F3C6}',
    feedback_received: '\u{1F4AC}',
    account_update: '\u{1F512}',
    announcement: '\u{1F4E2}',
  };

  return (
    <div className="notif-bell-wrapper" ref={dropdownRef}>
      <button className="notif-bell-btn" onClick={() => setOpen(!open)} aria-label="Notifications">
        {'\u{1F514}'}
        {unreadCount > 0 && (
          <span className="notif-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notif-dropdown">
          <div className="notif-dropdown-header">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <button className="notif-mark-all" onClick={markAllRead}>Mark all read</button>
            )}
          </div>
          <div className="notif-dropdown-list">
            {notifications.slice(0, 5).map(n => (
              <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`} onClick={() => handleClick(n)}>
                <span className="notif-icon">{typeIcon[n.type] || '\u{1F514}'}</span>
                <div className="notif-content">
                  <p className="notif-title">{n.title}</p>
                  <p className="notif-time">{new Date(n.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
            {notifications.length === 0 && <p className="notif-empty">No notifications yet</p>}
          </div>
          <a className="notif-view-all" href="/activity">View all activity</a>
        </div>
      )}
    </div>
  );
}

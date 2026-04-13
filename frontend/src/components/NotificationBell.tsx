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

  const handleClick = async (n: Notification) => {
    if (!n.is_read) await markRead(n.id);
    setOpen(false);
    if (n.link) window.location.href = n.link;
  };

  const typeIcon: Record<string, string> = {
    review_assigned: '✏️',
    review_received: '★',
    grade_posted:    '✓',
    feedback_received: '↩',
    account_update:  '⚙',
    announcement:    '📣',
  };

  return (
    <div className="notif-bell-wrapper" ref={dropdownRef}>
      <button className="notif-bell-btn" onClick={() => setOpen(!open)} aria-label="Notifications">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
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

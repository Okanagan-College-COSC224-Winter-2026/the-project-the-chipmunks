import { useState, useEffect, useCallback } from 'react';
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '../util/api';

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export function useNotifications() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const resp = await getUnreadCount();
      if (resp && resp.ok) {
        const data = await resp.json();
        setUnreadCount(data.unread_count);
      }
    } catch (err) {
      console.error('Failed to fetch unread count', err);
    }
  }, []);

  const fetchNotifications = useCallback(async (p = 1, type?: string) => {
    setLoading(true);
    try {
      const resp = await getNotifications(p, 20, type);
      if (resp && resp.ok) {
        const data = await resp.json();
        setNotifications(prev =>
          p === 1 ? data.notifications : [...prev, ...data.notifications]
        );
        setTotalPages(data.pages);
        setPage(p);
      }
    } catch (err) {
      console.error('Failed to fetch notifications', err);
    }
    setLoading(false);
  }, []);

  const markRead = useCallback(async (id: number) => {
    try {
      await markNotificationRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification read', err);
    }
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read', err);
    }
  }, []);

  // Poll unread count every 30 seconds
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  return {
    unreadCount,
    notifications,
    loading,
    page,
    totalPages,
    fetchNotifications,
    markRead,
    markAllRead,
    loadMore: () => fetchNotifications(page + 1),
  };
}

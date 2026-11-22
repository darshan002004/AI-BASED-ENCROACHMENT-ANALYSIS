import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { notificationsAPI } from '../services/api';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    const token = localStorage.getItem('encrowatch_token');
    if (!token) return;

    try {
      setLoading(true);
      const [listRes, countRes] = await Promise.all([
        notificationsAPI.list({ limit: 30 }),
        notificationsAPI.getUnreadCount(),
      ]);
      setNotifications(listRes.data?.items || []);
      setUnreadCount(countRes.data?.unread_count || 0);
    } catch (e) {
      // Gracefully silent on auth or network drops
      console.warn('Failed to fetch notifications:', e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();

    // Periodic poll every 30 seconds for background notifications
    const interval = setInterval(fetchNotifications, 30000);

    const token = localStorage.getItem('encrowatch_token');
    if (!token) {
      return () => clearInterval(interval);
    }

    // Connect WebSocket only when user is authenticated
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;
    let ws = null;
    let isDisposed = false;

    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        if (isDisposed) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'NEW_INCIDENT' || data.type === 'SLA_BREACH' || data.type === 'RESOLUTION_SUBMITTED') {
            fetchNotifications();
            showToast(data.title || 'Incident Update', data.message || 'New notification received.');
          }
        } catch (e) {
          // ignore malformed payloads
        }
      };
      ws.onerror = () => {
        // Suppress unhandled noisy errors in browser console
      };
    } catch (e) {
      // WebSocket gracefully unavailable
    }

    return () => {
      isDisposed = true;
      clearInterval(interval);
      if (ws) {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try { ws.close(); } catch (_) {}
          };
        } else if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.close();
          } catch (e) {}
        }
      }
    };
  }, [fetchNotifications]);

  const showToast = (title, message) => {
    setToast({ title, message });
    setTimeout(() => setToast(null), 4000);
  };

  const markRead = async (id) => {
    try {
      await notificationsAPI.markRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {
      console.error('Failed to mark notification read', e);
    }
  };

  const markAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.error('Failed to mark all notifications read', e);
    }
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        fetchNotifications,
        markRead,
        markAllRead,
        showToast,
      }}
    >
      {children}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center gap-3 border border-slate-700 animate-slide-up">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <div>
            <div className="text-sm font-semibold">{toast.title}</div>
            <div className="text-xs text-slate-300">{toast.message}</div>
          </div>
        </div>
      )}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => useContext(NotificationContext);

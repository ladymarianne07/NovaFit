/**
 * NotificationBell - In-app notification bell with unread badge and dropdown panel.
 * Polls the backend every 30 seconds. Follows NovaFitness design guidelines.
 */
import React, { useEffect, useRef, useState } from 'react'
import { Bell } from 'lucide-react'
import { notificationsAPI, NotificationResponse } from '../services/api'

const POLL_INTERVAL_MS = 30_000

const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const fetchNotifications = async () => {
    try {
      const data = await notificationsAPI.getNotifications()
      setNotifications(data.notifications)
      setUnreadCount(data.unread_count)
    } catch {
      // silently ignore — bell is non-critical
    }
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsAPI.markAsRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch {
      // ignore
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsAPI.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // ignore
    }
  }

  const formatDate = (iso: string) => {
    const date = new Date(iso)
    return date.toLocaleDateString('es-AR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="notif-bell-wrapper" ref={containerRef}>
      <button
        type="button"
        className={`dashboard-global-header-btn notif-bell-btn ${isOpen ? 'active' : ''}`}
        aria-label={`Notificaciones${unreadCount > 0 ? `, ${unreadCount} sin leer` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <Bell size={16} />
        <span>Alertas</span>
        {unreadCount > 0 && (
          <span className="notif-bell-badge" aria-hidden="true">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notif-panel" role="dialog" aria-label="Panel de notificaciones">
          <div className="notif-panel-header">
            <span className="notif-panel-title">Notificaciones</span>
            {unreadCount > 0 && (
              <button
                type="button"
                className="notif-panel-mark-all"
                onClick={handleMarkAllAsRead}
              >
                Marcar todas como leídas
              </button>
            )}
          </div>

          <div className="notif-panel-list">
            {notifications.length === 0 ? (
              <p className="notif-panel-empty">No tenés notificaciones</p>
            ) : (
              notifications.map((notif) => (
                <button
                  key={notif.id}
                  type="button"
                  className={`notif-item ${notif.is_read ? '' : 'notif-item--unread'}`}
                  onClick={() => !notif.is_read && handleMarkAsRead(notif.id)}
                >
                  {!notif.is_read && <span className="notif-item-dot" aria-hidden="true" />}
                  <div className="notif-item-body">
                    <p className="notif-item-title">{notif.title}</p>
                    <p className="notif-item-text">{notif.body}</p>
                    <p className="notif-item-date">{formatDate(notif.created_at)}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationBell

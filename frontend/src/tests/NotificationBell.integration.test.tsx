import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'

// ── API mock ────────────────────────────────────────────────────────────────

const mockGetNotifications = jest.fn()
const mockMarkAsRead = jest.fn()
const mockMarkAllAsRead = jest.fn()

jest.mock('../services/api', () => ({
  notificationsAPI: {
    getNotifications: (...args: unknown[]) => mockGetNotifications(...args),
    markAsRead: (...args: unknown[]) => mockMarkAsRead(...args),
    markAllAsRead: (...args: unknown[]) => mockMarkAllAsRead(...args),
  },
}))

import NotificationBell from '../components/NotificationBell'

// ── helpers ────────────────────────────────────────────────────────────────

const EMPTY_RESPONSE = { notifications: [], unread_count: 0 }

const ONE_UNREAD = {
  notifications: [
    { id: 1, type: 'invite_accepted', title: 'Nuevo alumno', body: 'Ana aceptó tu invitación', is_read: false, created_at: new Date().toISOString() },
  ],
  unread_count: 1,
}

const ONE_READ = {
  notifications: [
    { id: 2, type: 'trainer_edited_biometrics', title: 'Biométricos actualizados', body: 'Tu entrenador editó tu perfil', is_read: true, created_at: new Date().toISOString() },
  ],
  unread_count: 0,
}

// ── tests ──────────────────────────────────────────────────────────────────

describe('NotificationBell', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('renders bell button', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })
    expect(screen.getByRole('button', { name: /notificaciones/i })).toBeInTheDocument()
  })

  test('shows no badge when there are no unread notifications', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })
    expect(document.querySelector('.notif-bell-badge')).not.toBeInTheDocument()
  })

  test('shows badge with unread count', async () => {
    mockGetNotifications.mockResolvedValue(ONE_UNREAD)
    await act(async () => { render(<NotificationBell />) })
    await waitFor(() => {
      expect(document.querySelector('.notif-bell-badge')).toBeInTheDocument()
      expect(document.querySelector('.notif-bell-badge')).toHaveTextContent('1')
    })
  })

  test('opens dropdown panel on click', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(screen.getByRole('dialog', { name: /notificaciones/i })).toBeInTheDocument()
  })

  test('shows empty state when no notifications', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(screen.getByText(/no tenés notificaciones/i)).toBeInTheDocument()
  })

  test('shows notification content in panel', async () => {
    mockGetNotifications.mockResolvedValue(ONE_UNREAD)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    await waitFor(() => {
      expect(screen.getByText('Nuevo alumno')).toBeInTheDocument()
      expect(screen.getByText('Ana aceptó tu invitación')).toBeInTheDocument()
    })
  })

  test('shows mark-all-read button only when there are unread', async () => {
    mockGetNotifications.mockResolvedValue(ONE_UNREAD)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /marcar todas como leídas/i })).toBeInTheDocument()
    })
  })

  test('does not show mark-all-read when all are read', async () => {
    mockGetNotifications.mockResolvedValue(ONE_READ)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /marcar todas como leídas/i })).not.toBeInTheDocument()
    })
  })

  test('clicking unread notification calls markAsRead', async () => {
    mockGetNotifications.mockResolvedValue(ONE_UNREAD)
    mockMarkAsRead.mockResolvedValue(undefined)

    await act(async () => { render(<NotificationBell />) })
    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))

    await waitFor(() => expect(screen.getByText('Nuevo alumno')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Nuevo alumno').closest('button')!)
    await waitFor(() => expect(mockMarkAsRead).toHaveBeenCalledWith(1))
  })

  test('mark all as read clears badge', async () => {
    mockGetNotifications.mockResolvedValue(ONE_UNREAD)
    mockMarkAllAsRead.mockResolvedValue(undefined)

    await act(async () => { render(<NotificationBell />) })
    await waitFor(() => expect(document.querySelector('.notif-bell-badge')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /marcar todas como leídas/i })).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /marcar todas como leídas/i }))
    await waitFor(() => {
      expect(mockMarkAllAsRead).toHaveBeenCalled()
      expect(document.querySelector('.notif-bell-badge')).not.toBeInTheDocument()
    })
  })

  test('closes panel on Escape key', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(screen.getByRole('dialog', { name: /notificaciones/i })).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog', { name: /notificaciones/i })).not.toBeInTheDocument()
  })

  test('polls again after 30 seconds', async () => {
    mockGetNotifications.mockResolvedValue(EMPTY_RESPONSE)
    await act(async () => { render(<NotificationBell />) })

    expect(mockGetNotifications).toHaveBeenCalledTimes(1)
    await act(async () => { jest.advanceTimersByTime(30_000) })
    expect(mockGetNotifications).toHaveBeenCalledTimes(2)
  })
})

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// ── API mocks ────────────────────────────────────────────────────────────────

const mockGetActive = jest.fn()
const mockAdvanceSession = jest.fn()
const mockListSessions = jest.fn()
const mockGetDailyEnergy = jest.fn()
const mockLogSession = jest.fn()

jest.mock('../services/api', () => ({
  routineAPI: {
    getActive: (...args: unknown[]) => mockGetActive(...args),
    advanceSession: (...args: unknown[]) => mockAdvanceSession(...args),
    logSession: (...args: unknown[]) => mockLogSession(...args),
  },
  workoutAPI: {
    listSessions: (...args: unknown[]) => mockListSessions(...args),
    getDailyEnergy: (...args: unknown[]) => mockGetDailyEnergy(...args),
    createSession: jest.fn(),
    deleteSession: jest.fn(),
  },
}))

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { objective: 'body_recomp' } }),
}))

jest.mock('../components/RoutineModule', () => () => <div data-testid="routine-module" />)

import WorkoutModule from '../components/WorkoutModule'

// ── Fixtures ─────────────────────────────────────────────────────────────────

const SESSION_A = {
  id: 'session_a',
  day: 'Lunes',
  label: 'A',
  day_label: 'Día 1 · Pecho y Espalda',
  title: 'Pecho y Espalda',
  color: '#c8f55a',
  estimated_calories_per_session: 320,
  exercises: [
    { id: 'ex1', name: 'Press de banca', muscle: 'Pectoral', group: 'Empuje', estimated_calories: 45 },
  ],
}

const SESSION_B = {
  id: 'session_b',
  day: 'Martes',
  label: 'B',
  day_label: 'Día 2 · Pierna',
  title: 'Pierna',
  color: '#ff6b6b',
  estimated_calories_per_session: 380,
  exercises: [
    { id: 'ex2', name: 'Sentadilla', muscle: 'Cuádriceps', group: 'Piernas', estimated_calories: 60 },
  ],
}

const ROUTINE_AT_INDEX_0 = {
  id: 1,
  status: 'ready',
  source_type: 'ai_text',
  current_session_index: 0,
  routine_data: {
    title: 'Mi Rutina Test',
    sessions: [SESSION_A, SESSION_B],
  },
  intake_data: { session_duration_minutes: 60 },
}

const ROUTINE_AT_INDEX_1 = {
  ...ROUTINE_AT_INDEX_0,
  current_session_index: 1,
}

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks()
  mockListSessions.mockResolvedValue([])
  mockGetDailyEnergy.mockResolvedValue({ exercise_kcal_est: 0, intake_kcal: 0, net_kcal_est: 0 })
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('WorkoutModule — Mis Entrenos tab', () => {
  it('shows empty state when no active routine', async () => {
    mockGetActive.mockRejectedValue(new Error('not found'))

    render(<WorkoutModule />)

    await waitFor(() => {
      expect(screen.getByText(/sin entreno programado/i)).toBeInTheDocument()
    })
  })

  it('shows current session by index (index 0 → session A)', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_0)

    render(<WorkoutModule />)

    await waitFor(() => {
      expect(screen.getByText('Pecho y Espalda')).toBeInTheDocument()
    })
    expect(screen.getByText(/próximo entrenamiento/i)).toBeInTheDocument()
    expect(screen.getByText(/320 kcal/i)).toBeInTheDocument()
  })

  it('shows session B when index is 1', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_1)

    render(<WorkoutModule />)

    await waitFor(() => {
      expect(screen.getByText('Pierna')).toBeInTheDocument()
    })
  })

  it('opens log modal when Completar is clicked', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_0)
    mockListSessions.mockResolvedValue([])
    mockGetDailyEnergy.mockResolvedValue({ exercise_kcal_est: 0, intake_kcal: 0, net_kcal_est: 0 })

    render(<WorkoutModule />)

    await waitFor(() => screen.getByText('Pecho y Espalda'))

    fireEvent.click(screen.getByRole('button', { name: /marcar entrenamiento como completado/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /registrar entrenamiento/i })).toBeInTheDocument()
    })
  })

  it('advances session index after confirming log modal', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_0)
    mockListSessions.mockResolvedValue([])
    mockGetDailyEnergy.mockResolvedValue({ exercise_kcal_est: 0, intake_kcal: 0, net_kcal_est: 0 })
    mockLogSession.mockResolvedValue({ id: 1, total_kcal_est: 310 })
    mockAdvanceSession.mockResolvedValue(ROUTINE_AT_INDEX_1)

    render(<WorkoutModule />)

    await waitFor(() => screen.getByText('Pecho y Espalda'))

    fireEvent.click(screen.getByRole('button', { name: /marcar entrenamiento como completado/i }))
    await waitFor(() => screen.getByRole('dialog', { name: /registrar entrenamiento/i }))

    fireEvent.click(screen.getByRole('button', { name: /sí, la completé/i }))

    await waitFor(() => {
      expect(mockLogSession).toHaveBeenCalled()
      expect(mockAdvanceSession).toHaveBeenCalledWith({ action: 'skip' })
    })
  })

  it('calls advanceSession with skip when Saltar is clicked', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_0)
    mockAdvanceSession.mockResolvedValue(ROUTINE_AT_INDEX_1)

    render(<WorkoutModule />)

    await waitFor(() => screen.getByText('Pecho y Espalda'))

    fireEvent.click(screen.getByRole('button', { name: /saltar este entrenamiento/i }))

    await waitFor(() => {
      expect(mockAdvanceSession).toHaveBeenCalledWith({ action: 'skip' })
    })
  })

  it('advances to next session after skip', async () => {
    mockGetActive.mockResolvedValue(ROUTINE_AT_INDEX_0)
    mockAdvanceSession.mockResolvedValue(ROUTINE_AT_INDEX_1)

    render(<WorkoutModule />)

    await waitFor(() => screen.getByText('Pecho y Espalda'))

    fireEvent.click(screen.getByRole('button', { name: /saltar este entrenamiento/i }))

    await waitFor(() => {
      expect(screen.getByText('Pierna')).toBeInTheDocument()
    })
  })
})

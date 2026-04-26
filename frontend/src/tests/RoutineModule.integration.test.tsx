import React from 'react'
import { render, screen, fireEvent, waitFor, act, within } from '@testing-library/react'

// ── API mock ────────────────────────────────────────────────────────────────

const mockGetActive = jest.fn()
const mockGenerateFromText = jest.fn()
const mockEditRoutine = jest.fn()
const mockUpload = jest.fn()
const mockLogSession = jest.fn()

jest.mock('../services/api', () => ({
  routineAPI: {
    getActive: (...args: unknown[]) => mockGetActive(...args),
    generateFromText: (...args: unknown[]) => mockGenerateFromText(...args),
    editRoutine: (...args: unknown[]) => mockEditRoutine(...args),
    upload: (...args: unknown[]) => mockUpload(...args),
    logSession: (...args: unknown[]) => mockLogSession(...args),
  },
}))

// ── Auth mock ────────────────────────────────────────────────────────────────

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { objective: 'body_recomp' } }),
}))

import RoutineModule from '../components/RoutineModule'

// ── Fixtures ────────────────────────────────────────────────────────────────

const SAMPLE_ROUTINE = {
  id: 1,
  status: 'ready',
  source_type: 'ai_text',
  html_content: '<html><body>Rutina</body></html>',
  health_analysis: null,
  intake_data: { objective: 'body_recomp', duration_months: 1 },
  error_message: null,
  routine_data: {
    title: 'Full Body 3 días',
    subtitle: 'Ciclo 1 mes',
    sessions: [
      {
        id: 'full_a',
        color: '#c8f55a',
        label: 'Full Body A',
        day_label: 'Lunes · Full Body A',
        title: 'Piernas + Empuje',
        session_duration_minutes: 60,
        exercises: [
          { id: 'e1', name: 'Sentadilla', muscle: 'Cuádriceps', group: 'Piernas', sets: '3', reps: '12', rest_seconds: 90, notes: '' },
        ],
      },
    ],
  },
  created_at: '2026-03-21T00:00:00Z',
  updated_at: '2026-03-21T00:00:00Z',
}

const MULTI_PHASE_ROUTINE = {
  ...SAMPLE_ROUTINE,
  routine_data: {
    ...SAMPLE_ROUTINE.routine_data,
    month_data: [
      { month: 1, sets: '3', reps: '15-20', rest_seconds: 60, note: 'Adaptación' },
      { month: 2, sets: '4', reps: '8-12', rest_seconds: 90, note: 'Fuerza' },
    ],
    sessions: [
      {
        ...SAMPLE_ROUTINE.routine_data.sessions[0],
        exercises: [
          {
            id: 'e1', name: 'Sentadilla', muscle: 'Cuádriceps', group: 'Piernas',
            notes: '',
          },
        ],
      },
    ],
  },
}

// ── helpers ──────────────────────────────────────────────────────────────────

const renderModule = () => render(<RoutineModule />)

// ── tests ────────────────────────────────────────────────────────────────────

describe('RoutineModule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ── Loading & empty state ─────────────────────────────────────────────────

  test('shows loading state initially', () => {
    mockGetActive.mockReturnValue(new Promise(() => {})) // never resolves
    renderModule()
    expect(screen.getByText(/cargando rutina/i)).toBeInTheDocument()
  })

  test('shows empty state when no active routine', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    expect(screen.getByText(/todavía no tenés una rutina/i)).toBeInTheDocument()
  })

  test('shows "Crear mi rutina" CTA when empty', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    expect(screen.getByRole('button', { name: /crear mi rutina/i })).toBeInTheDocument()
  })

  // ── Create modal opens ────────────────────────────────────────────────────

  test('clicking "Crear mi rutina" CTA opens create modal', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    expect(screen.getByRole('dialog', { name: /crear mi rutina/i })).toBeInTheDocument()
  })

  test('create modal shows AI/File mode buttons', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    expect(screen.getByRole('button', { name: /crear con ia/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /subir archivo/i })).toBeInTheDocument()
  })

  test('create modal can be closed', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    const dialog = screen.getByRole('dialog', { name: /crear mi rutina/i })
    expect(dialog).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /cerrar/i }))
    expect(screen.queryByRole('dialog', { name: /crear mi rutina/i })).not.toBeInTheDocument()
  })

  // ── Routine loaded ────────────────────────────────────────────────────────

  test('displays routine title when active routine exists', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByText('Full Body 3 días')).toBeInTheDocument()
  })

  test('displays routine subtitle', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByText('Ciclo 1 mes')).toBeInTheDocument()
  })

  test('displays ai source badge', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByText(/generada con ia/i)).toBeInTheDocument()
  })

  test('displays session cards', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByText('Piernas + Empuje')).toBeInTheDocument()
    expect(screen.getByText('350 kcal est.')).toBeInTheDocument()
  })

  test('"Reemplazar" button shown when routine exists', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByRole('button', { name: /reemplazar/i })).toBeInTheDocument()
  })

  test('"Reemplazar" button opens create modal', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /reemplazar/i }))
    expect(screen.getByRole('dialog', { name: /reemplazar rutina/i })).toBeInTheDocument()
  })

  // ── Edit bar ──────────────────────────────────────────────────────────────

  test('edit bar hidden by default', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.queryByText(/describí qué querés cambiar/i)).not.toBeInTheDocument()
  })

  test('clicking "Pedir cambios" shows edit bar', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /pedir cambios/i }))
    expect(screen.getByText(/describí qué querés cambiar/i)).toBeInTheDocument()
  })

  test('edit bar apply button disabled when text is too short', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /pedir cambios/i }))
    expect(screen.getByRole('button', { name: /aplicar/i })).toBeDisabled()
  })

  test('edit routine calls API and updates routine', async () => {
    const updated = { ...SAMPLE_ROUTINE, routine_data: { ...SAMPLE_ROUTINE.routine_data, title: 'Rutina Editada' } }
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    mockEditRoutine.mockResolvedValue(updated)

    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /pedir cambios/i }))

    const textarea = screen.getByPlaceholderText(/ej: agregá más ejercicios/i)
    fireEvent.change(textarea, { target: { value: 'Agregar más ejercicios de espalda' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /aplicar/i }))
    })

    await waitFor(() => expect(mockEditRoutine).toHaveBeenCalledWith({ edit_instruction: 'Agregar más ejercicios de espalda' }))
    await waitFor(() => expect(screen.getByText('Rutina Editada')).toBeInTheDocument())
  })

  // ── AI generation ─────────────────────────────────────────────────────────

  test('AI create form shows intake form fields', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    expect(screen.getByText(/condiciones de salud/i)).toBeInTheDocument()
    expect(screen.getByText(/frecuencia/i)).toBeInTheDocument()
    expect(screen.getByText(/lesiones actuales o recientes/i)).toBeInTheDocument()
  })

  test('shows missing data modal when required fields empty', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))

    // health_conditions is empty by default — trigger validation
    const healthTextarea = screen.getAllByPlaceholderText(/hernia lumbar/i)[0]
    fireEvent.change(healthTextarea, { target: { value: '' } })

    fireEvent.click(screen.getByRole('button', { name: /generar mi rutina personalizada/i }))
    expect(await screen.findByRole('dialog', { name: /datos faltantes/i })).toBeInTheDocument()
  })

  test('missing data modal lists injuries as required field', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    fireEvent.click(screen.getByRole('button', { name: /generar mi rutina personalizada/i }))
    const dialog = await screen.findByRole('dialog', { name: /datos faltantes/i })
    expect(within(dialog).getByText(/lesiones actuales o recientes/i)).toBeInTheDocument()
  })

  test('missing data modal has "Completar datos" and "La IA infiere" buttons', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    fireEvent.click(screen.getByRole('button', { name: /generar mi rutina personalizada/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /completar datos/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /la ia infiere/i })).toBeInTheDocument()
    })
  })

  test('"La IA infiere" triggers generation without required fields', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    mockGenerateFromText.mockResolvedValue(SAMPLE_ROUTINE)

    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    fireEvent.click(screen.getByRole('button', { name: /generar mi rutina personalizada/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /la ia infiere/i })).toBeInTheDocument())

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /la ia infiere/i }))
    })

    await waitFor(() => expect(mockGenerateFromText).toHaveBeenCalled())
  })

  test('generate success closes modal and shows routine title', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    mockGenerateFromText.mockResolvedValue(SAMPLE_ROUTINE)

    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))

    // Fill all required fields so missing-data modal is skipped
    const healthTextarea = screen.getAllByPlaceholderText(/hernia lumbar/i)[0]
    fireEvent.change(healthTextarea, { target: { value: 'ninguna' } })
    const injuriesTextarea = screen.getByPlaceholderText(/esguince de tobillo/i)
    fireEvent.change(injuriesTextarea, { target: { value: 'ninguna' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /generar mi rutina personalizada/i }))
    })

    await waitFor(() => expect(screen.getByText('Full Body 3 días')).toBeInTheDocument())
    // Modal should be closed
    expect(screen.queryByRole('dialog', { name: /crear mi rutina/i })).not.toBeInTheDocument()
  })

  // ── File upload mode ──────────────────────────────────────────────────────

  test('file mode shows disclaimer and dropzone', async () => {
    mockGetActive.mockRejectedValue(new Error('404'))
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /crear mi rutina/i }))
    fireEvent.click(screen.getByRole('button', { name: /subir archivo/i }))

    expect(screen.getByText(/información requerida en el archivo/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /seleccionar archivo de rutina/i })).toBeInTheDocument()
  })

  // ── Log session modal ─────────────────────────────────────────────────────

  test('"Registrar sesión" button opens log modal', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /registrar sesión/i }))
    expect(screen.getByRole('dialog', { name: /registrar entrenamiento/i })).toBeInTheDocument()
  })

  test('log modal step 1 shows "Sí, la completé" and "Ajustar sesión" options', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /registrar sesión/i }))
    expect(screen.getByRole('button', { name: /sí, la completé/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ajustar sesión/i })).toBeInTheDocument()
  })

  test('"Ajustar sesión" moves to step 2 with exercise checkboxes', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /registrar sesión/i }))
    fireEvent.click(screen.getByRole('button', { name: /ajustar sesión/i }))
    expect(screen.getByText(/marcá los ejercicios que/i)).toBeInTheDocument()
    expect(screen.getByText('Sentadilla')).toBeInTheDocument()
  })

  test('"Agregar ejercicio extra" button appears in step 2', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /registrar sesión/i }))
    fireEvent.click(screen.getByRole('button', { name: /ajustar sesión/i }))
    expect(screen.getByRole('button', { name: /agregar ejercicio extra/i })).toBeInTheDocument()
  })

  test('"Sí, la completé" calls logSession and closes modal', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    mockLogSession.mockResolvedValue({ id: 1, total_kcal_est: 279 })
    await act(async () => { renderModule() })
    fireEvent.click(screen.getByRole('button', { name: /registrar sesión/i }))
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /sí, la completé/i }))
    })
    await waitFor(() => expect(mockLogSession).toHaveBeenCalledWith(
      expect.objectContaining({ session_id: 'full_a', skipped_exercise_ids: [], extra_exercises: [] })
    ))
    expect(screen.queryByRole('dialog', { name: /registrar entrenamiento/i })).not.toBeInTheDocument()
  })

  // ── Session card expand ───────────────────────────────────────────────────

  test('clicking session card expands exercise list', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.queryByText(/3 × 12/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /lunes · full body a/i }))
    expect(screen.getByText('Sentadilla')).toBeInTheDocument()
  })

  // ── Month tabs ────────────────────────────────────────────────────────────

  test('month tabs not shown for single-phase routine', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.queryByRole('tab', { name: /mes 1/i })).not.toBeInTheDocument()
  })

  test('month tabs shown for multi-phase routine', async () => {
    mockGetActive.mockResolvedValue(MULTI_PHASE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.getByRole('tab', { name: /mes 1/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /mes 2/i })).toBeInTheDocument()
  })

  test('switching month tab updates exercise sets/reps display', async () => {
    mockGetActive.mockResolvedValue(MULTI_PHASE_ROUTINE)
    await act(async () => { renderModule() })
    // expand session card
    fireEvent.click(screen.getByRole('button', { name: /lunes · full body a/i }))
    // default month 1 → 3 × 15-20
    expect(screen.getByText(/3 × 15-20/)).toBeInTheDocument()
    // switch to month 2
    fireEvent.click(screen.getByRole('tab', { name: /mes 2/i }))
    expect(screen.getByText(/4 × 8-12/)).toBeInTheDocument()
  })

  // ── Health warning ────────────────────────────────────────────────────────

  test('health warning displayed when routine has warning', async () => {
    const withWarning = {
      ...SAMPLE_ROUTINE,
      health_analysis: { warning: 'Consultá a tu médico antes de iniciar.', conditions_detected: [], contraindications_applied: [], adaptations: [] },
    }
    mockGetActive.mockResolvedValue(withWarning)
    await act(async () => { renderModule() })
    expect(screen.getByText(/consultá a tu médico/i)).toBeInTheDocument()
  })

  test('no health warning section when warning is null', async () => {
    mockGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    await act(async () => { renderModule() })
    expect(screen.queryByText(/consultá a tu médico/i)).not.toBeInTheDocument()
  })
})

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// ── API mock ─────────────────────────────────────────────────────────────────

const mockDietGetActive = jest.fn()
const mockDietGenerate = jest.fn()
const mockDietEdit = jest.fn()
const mockRoutineGetActive = jest.fn()

jest.mock('../services/api', () => ({
  dietAPI: {
    getActive: (...args: unknown[]) => mockDietGetActive(...args),
    generate: (...args: unknown[]) => mockDietGenerate(...args),
    edit: (...args: unknown[]) => mockDietEdit(...args),
  },
  routineAPI: {
    getActive: (...args: unknown[]) => mockRoutineGetActive(...args),
  },
}))

// ── Auth mock ─────────────────────────────────────────────────────────────────

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      target_calories: 2000,
      bmr: 1600,
      objective: 'body_recomp',
    },
  }),
}))

import DietModule from '../components/DietModule'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const SAMPLE_DIET_RESPONSE = {
  id: 1,
  status: 'ready',
  error_message: null,
  current_meal_index: 0,
  current_meal_date: null,
  diet_data: {
    title: 'Plan de alimentación personalizado',
    description: 'Dieta de prueba.',
    objective_label: 'Recomposición corporal',
    target_calories_rest: 1800,
    target_calories_training: 2100,
    target_protein_g: 120,
    target_carbs_g: 200,
    target_fat_g: 55,
    water_ml_rest: 2100,
    water_ml_training: 2600,
    water_notes: 'Basado en peso corporal.',
    training_days: ['lunes', 'miércoles', 'viernes'],
    training_day: {
      day_type: 'training',
      label: 'Día de entrenamiento',
      total_calories: 2100,
      total_protein_g: 130,
      total_carbs_g: 230,
      total_fat_g: 57,
      water_ml: 2600,
      notes: '',
      meals: [
        {
          id: 'breakfast',
          name: 'Desayuno',
          total_calories: 420,
          total_protein_g: 25,
          total_carbs_g: 55,
          total_fat_g: 10,
          notes: '',
          foods: [{ name: 'Avena', portion: '80g', calories: 350, protein_g: 18, carbs_g: 52, fat_g: 6, notes: '' }],
        },
      ],
    },
    rest_day: {
      day_type: 'rest',
      label: 'Día de descanso',
      total_calories: 1800,
      total_protein_g: 120,
      total_carbs_g: 180,
      total_fat_g: 52,
      water_ml: 2100,
      notes: '',
      meals: [
        {
          id: 'breakfast',
          name: 'Desayuno',
          total_calories: 400,
          total_protein_g: 22,
          total_carbs_g: 50,
          total_fat_g: 10,
          notes: '',
          foods: [{ name: 'Tostadas', portion: '2 tostadas', calories: 280, protein_g: 14, carbs_g: 32, fat_g: 9, notes: '' }],
        },
      ],
    },
    health_notes: ['Mantener buena hidratación.'],
    supplement_suggestions: '',
    nutritional_summary: 'Plan equilibrado.',
  },
  created_at: '2026-03-21T00:00:00Z',
  updated_at: '2026-03-21T00:00:00Z',
}

const SAMPLE_ROUTINE = {
  id: 1,
  status: 'ready',
  intake_data: { frequency_days: '3-4' },
  routine_data: { title: 'Mi rutina', sessions: [] },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const renderModule = () => render(<DietModule />)

const openCreateModal = async () => {
  await waitFor(() => screen.getByText(/generar mi dieta con ia/i))
  fireEvent.click(screen.getByText(/generar mi dieta con ia/i))
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('DietModule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ── Loading & empty state ────────────────────────────────────────────────

  test('shows loading state initially', () => {
    mockDietGetActive.mockReturnValue(new Promise(() => {}))
    renderModule()
    expect(screen.getByText(/cargando/i)).toBeInTheDocument()
  })

  test('shows empty state when no diet exists', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    renderModule()
    await waitFor(() => {
      expect(screen.getByText(/todavía no tenés un plan de dieta/i)).toBeInTheDocument()
    })
  })

  // ── Active diet display ───────────────────────────────────────────────────

  test('renders active diet title when one exists', async () => {
    mockDietGetActive.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await waitFor(() => {
      expect(screen.getByText(/Plan de alimentación personalizado/i)).toBeInTheDocument()
    })
  })

  // ── Create modal ─────────────────────────────────────────────────────────

  test('opens create modal showing training days section', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    renderModule()
    await openCreateModal()
    await waitFor(() => {
      expect(screen.getByText(/Días de entrenamiento/i)).toBeInTheDocument()
    })
  })

  // ── Training days checkboxes ──────────────────────────────────────────────

  test('renders all 7 day-of-week chips in create modal', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    renderModule()
    await openCreateModal()

    await waitFor(() => {
      expect(screen.getByText('Lu')).toBeInTheDocument()
      expect(screen.getByText('Ma')).toBeInTheDocument()
      expect(screen.getByText('Mi')).toBeInTheDocument()
      expect(screen.getByText('Ju')).toBeInTheDocument()
      expect(screen.getByText('Vi')).toBeInTheDocument()
      expect(screen.getByText('Sá')).toBeInTheDocument()
      expect(screen.getByText('Do')).toBeInTheDocument()
    })
  })

  test('toggles a training day chip on click', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    renderModule()
    await openCreateModal()

    await waitFor(() => screen.getByText('Lu'))
    const lunesChip = screen.getByText('Lu').closest('button')!
    expect(lunesChip).not.toHaveClass('active')
    fireEvent.click(lunesChip)
    expect(lunesChip).toHaveClass('active')
  })

  // ── Suggested days from routine ───────────────────────────────────────────

  test('shows suggested days banner when routine has frequency_days', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    renderModule()
    await openCreateModal()

    await waitFor(() => {
      expect(screen.getByText(/Tu rutina sugiere/i)).toBeInTheDocument()
    })
  })

  test('applies suggested days when "Usar estos días" is clicked', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockResolvedValue(SAMPLE_ROUTINE)
    mockDietGenerate.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await openCreateModal()

    await waitFor(() => screen.getByText(/Usar estos días/i))
    fireEvent.click(screen.getByText(/Usar estos días/i))

    // After applying, generate should be called with the suggested days (lunes, miércoles, viernes)
    const generateBtn = screen.getByRole('button', { name: /Generar mi dieta personalizada/i })
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(mockDietGenerate).toHaveBeenCalledWith(
        expect.objectContaining({
          intake: expect.objectContaining({
            training_days: expect.arrayContaining(['lunes', 'miércoles', 'viernes']),
          }),
        }),
      )
    })
  })

  // ── Diet generation ───────────────────────────────────────────────────────

  test('calls dietAPI.generate with selected training_days in payload', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    mockDietGenerate.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await openCreateModal()

    await waitFor(() => screen.getByText('Lu'))
    fireEvent.click(screen.getByText('Lu').closest('button')!)
    fireEvent.click(screen.getByText('Vi').closest('button')!)

    fireEvent.click(screen.getByRole('button', { name: /Generar mi dieta personalizada/i }))

    await waitFor(() => {
      expect(mockDietGenerate).toHaveBeenCalledWith(
        expect.objectContaining({
          intake: expect.objectContaining({
            training_days: expect.arrayContaining(['lunes', 'viernes']),
          }),
        }),
      )
    })
  })

  test('closes modal and shows diet title after successful generation', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    mockDietGenerate.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await openCreateModal()

    await waitFor(() => screen.getByRole('button', { name: /Generar mi dieta personalizada/i }))
    fireEvent.click(screen.getByRole('button', { name: /Generar mi dieta personalizada/i }))

    await waitFor(() => {
      expect(screen.getByText(/Plan de alimentación personalizado/i)).toBeInTheDocument()
    })
    // Modal section should be gone
    expect(screen.queryByText(/Días de entrenamiento/i)).not.toBeInTheDocument()
  })

  test('shows error message when generation fails', async () => {
    mockDietGetActive.mockRejectedValue(new Error('Not found'))
    mockRoutineGetActive.mockRejectedValue(new Error('No routine'))
    mockDietGenerate.mockRejectedValue(new Error('Gemini timeout'))
    renderModule()
    await openCreateModal()

    await waitFor(() => screen.getByRole('button', { name: /Generar mi dieta personalizada/i }))
    fireEvent.click(screen.getByRole('button', { name: /Generar mi dieta personalizada/i }))

    await waitFor(() => {
      expect(screen.getByText(/Gemini timeout/i)).toBeInTheDocument()
    })
  })

  // ── Diet display — day tabs ───────────────────────────────────────────────

  test('shows training day tab content by default', async () => {
    mockDietGetActive.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await waitFor(() => {
      expect(screen.getByText('Día de Entreno')).toBeInTheDocument()
    })
  })

  test('switches to rest day when rest tab is clicked', async () => {
    mockDietGetActive.mockResolvedValue(SAMPLE_DIET_RESPONSE)
    renderModule()
    await waitFor(() => screen.getByText('Día de Descanso'))

    fireEvent.click(screen.getByText('Día de Descanso'))

    // After clicking, rest day data should be shown — label from diet_data.rest_day.label
    await waitFor(() => {
      expect(screen.getByText(/Día de descanso/i)).toBeInTheDocument()
    })
  })
})

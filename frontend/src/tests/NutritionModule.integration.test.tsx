/**
 * NutritionModule integration tests — logged meals list + alternative meal flow.
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// ── API mock ──────────────────────────────────────────────────────────────────

const mockGetMeals = jest.fn()
const mockDeleteMeal = jest.fn()
const mockGetCurrentMeal = jest.fn()
const mockLogMeal = jest.fn()
const mockGetMealAlternative = jest.fn()
const mockApplyMealAlternative = jest.fn()
const mockFoodParsePreview = jest.fn()
const mockFoodConfirmAndLog = jest.fn()

jest.mock('../services/api', () => ({
  nutritionAPI: {
    getMeals: (...args: unknown[]) => mockGetMeals(...args),
    deleteMeal: (...args: unknown[]) => mockDeleteMeal(...args),
  },
  dietAPI: {
    getCurrentMeal: (...args: unknown[]) => mockGetCurrentMeal(...args),
    logMeal: (...args: unknown[]) => mockLogMeal(...args),
    getMealAlternative: (...args: unknown[]) => mockGetMealAlternative(...args),
    applyMealAlternative: (...args: unknown[]) => mockApplyMealAlternative(...args),
  },
  foodAPI: {
    parsePreview: (...args: unknown[]) => mockFoodParsePreview(...args),
    confirmAndLog: (...args: unknown[]) => mockFoodConfirmAndLog(...args),
  },
}))

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1 } }),
}))

// AiMealConfirmModal is not needed for these tests
jest.mock('../components/AiMealConfirmModal', () => ({
  __esModule: true,
  default: () => null,
}))

import NutritionModule from '../components/NutritionModule'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const SAMPLE_LOGGED_MEAL = {
  id: 'meal-1',
  meal_type: 'breakfast',
  meal_label: 'Desayuno',
  event_timestamp: new Date().toISOString(),
  items: [
    { food_name: 'oatmeal', grams: 80 },
    { food_name: 'banana', grams: 120 },
  ],
  total_calories: 430,
  total_protein: 12,
  total_carbs: 75,
  total_fat: 8,
}

const SAMPLE_CURRENT_MEAL = {
  day_type: 'training_day',
  meal: {
    id: 'breakfast',
    name: 'Desayuno',
    time: '07:30',
    foods: [
      { name: 'Avena', portion: '80g', calories: 280, protein_g: 10, carbs_g: 48, fat_g: 5, notes: '' },
      { name: 'Leche', portion: '200ml', calories: 100, protein_g: 7, carbs_g: 10, fat_g: 4, notes: '' },
    ],
    total_calories: 380,
    total_protein_g: 17,
    total_carbs_g: 58,
    total_fat_g: 9,
    notes: '',
  },
  meal_index: 0,
  total_meals: 3,
  is_last_meal: false,
  is_overridden: false,
}

const SAMPLE_ALTERNATIVE = {
  meal: {
    id: 'meal_alt',
    name: 'Desayuno alternativo',
    time: '',
    foods: [
      { name: 'Yogur griego', portion: '200g', calories: 180, protein_g: 15, carbs_g: 12, fat_g: 5, notes: '' },
      { name: 'Granola', portion: '40g', calories: 180, protein_g: 4, carbs_g: 30, fat_g: 6, notes: '' },
    ],
    total_calories: 360,
    total_protein_g: 19,
    total_carbs_g: 42,
    total_fat_g: 11,
    notes: '',
  },
  day_type: 'training_day',
  meal_index: 0,
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const renderModule = () => render(<NutritionModule />)

beforeEach(() => {
  jest.clearAllMocks()
  mockGetMeals.mockResolvedValue([])
  mockGetCurrentMeal.mockResolvedValue(SAMPLE_CURRENT_MEAL)
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('Logged meals list', () => {
  it('renders empty state when no meals logged', async () => {
    mockGetMeals.mockResolvedValue([])
    renderModule()
    await waitFor(() => {
      expect(screen.getByText(/hoy todavía no cargaste comidas/i)).toBeInTheDocument()
    })
  })

  it('renders logged meal as a card with inline ingredients', async () => {
    mockGetMeals.mockResolvedValue([SAMPLE_LOGGED_MEAL])
    renderModule()
    await waitFor(() => {
      expect(screen.getAllByText('Desayuno').length).toBeGreaterThanOrEqual(1)
      // Ingredients rendered as a single inline string with · separator
      const ingredientEl = screen.getByText((text) =>
        (text.includes('avena') || text.includes('oatmeal')) &&
        (text.includes('banana'))
      )
      expect(ingredientEl).toBeInTheDocument()
    })
  })

  it('shows macro pills for each logged meal', async () => {
    mockGetMeals.mockResolvedValue([SAMPLE_LOGGED_MEAL])
    renderModule()
    await waitFor(() => {
      // "430 kcal" appears in the name row and in the macro pill
      expect(screen.getAllByText(/430 kcal/).length).toBeGreaterThanOrEqual(1)
      // "Carbos:" appears in both the tracker card and the logged meal pill
      expect(screen.getAllByText(/Carbos:/i).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders delete button for each meal', async () => {
    mockGetMeals.mockResolvedValue([SAMPLE_LOGGED_MEAL])
    mockDeleteMeal.mockResolvedValue(undefined)
    renderModule()
    await waitFor(() => {
      const deleteBtn = screen.getByLabelText('Eliminar comida')
      expect(deleteBtn).toBeInTheDocument()
    })
  })

  it('renders multiple meals as separate cards', async () => {
    const secondMeal = { ...SAMPLE_LOGGED_MEAL, id: 'meal-2', meal_label: 'Almuerzo', meal_type: 'lunch' }
    mockGetMeals.mockResolvedValue([SAMPLE_LOGGED_MEAL, secondMeal])
    renderModule()
    await waitFor(() => {
      // Both text values appear in badge + name; use getAllByText to handle duplicates
      expect(screen.getAllByText('Desayuno').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Almuerzo').length).toBeGreaterThanOrEqual(1)
    })
  })
})

describe('Meal tracker — Alternativa button', () => {
  it('renders Alternativa button when current meal exists', async () => {
    renderModule()
    await waitFor(() => {
      expect(screen.getByLabelText('Obtener comida alternativa')).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching alternative', async () => {
    mockGetMealAlternative.mockImplementation(() => new Promise(() => {})) // never resolves
    renderModule()
    await waitFor(() => screen.getByLabelText('Obtener comida alternativa'))
    fireEvent.click(screen.getByLabelText('Obtener comida alternativa'))
    await waitFor(() => {
      // Button should be disabled while loading
      expect(screen.getByLabelText('Obtener comida alternativa')).toBeDisabled()
    })
  })

  it('opens alternative modal after successful fetch', async () => {
    mockGetMealAlternative.mockResolvedValue(SAMPLE_ALTERNATIVE)
    renderModule()
    await waitFor(() => screen.getByLabelText('Obtener comida alternativa'))
    fireEvent.click(screen.getByLabelText('Obtener comida alternativa'))
    await waitFor(() => {
      expect(screen.getByText('Alternativa sugerida')).toBeInTheDocument()
      expect(screen.getByText('Desayuno alternativo')).toBeInTheDocument()
    })
  })
})

describe('Alternative meal modal', () => {
  const openModal = async () => {
    mockGetMealAlternative.mockResolvedValue(SAMPLE_ALTERNATIVE)
    renderModule()
    await waitFor(() => screen.getByLabelText('Obtener comida alternativa'))
    fireEvent.click(screen.getByLabelText('Obtener comida alternativa'))
    await waitFor(() => screen.getByText('Alternativa sugerida'))
  }

  it('shows meal details including inline ingredients', async () => {
    await openModal()
    expect(screen.getByText(/Yogur griego/i)).toBeInTheDocument()
    // 360 kcal appears in both name-row and macro pill — at least one instance should be present
    expect(screen.getAllByText(/360 kcal/).length).toBeGreaterThanOrEqual(1)
  })

  it('has Reemplazar en mi dieta and Solo por hoy buttons', async () => {
    await openModal()
    expect(screen.getByText('Reemplazar en mi dieta')).toBeInTheDocument()
    expect(screen.getByText('Solo por hoy (24 hs)')).toBeInTheDocument()
    expect(screen.getByText('Descartar')).toBeInTheDocument()
  })

  it('calls applyMealAlternative with scope=diet when clicking Reemplazar', async () => {
    mockApplyMealAlternative.mockResolvedValue(undefined)
    mockGetCurrentMeal.mockResolvedValue({ ...SAMPLE_CURRENT_MEAL, is_overridden: false })
    await openModal()
    fireEvent.click(screen.getByText('Reemplazar en mi dieta'))
    await waitFor(() => {
      expect(mockApplyMealAlternative).toHaveBeenCalledWith(
        expect.objectContaining({ scope: 'diet', meal_index: 0 })
      )
    })
  })

  it('calls applyMealAlternative with scope=today when clicking Solo por hoy', async () => {
    mockApplyMealAlternative.mockResolvedValue(undefined)
    mockGetCurrentMeal.mockResolvedValue({ ...SAMPLE_CURRENT_MEAL, is_overridden: true })
    await openModal()
    fireEvent.click(screen.getByText('Solo por hoy (24 hs)'))
    await waitFor(() => {
      expect(mockApplyMealAlternative).toHaveBeenCalledWith(
        expect.objectContaining({ scope: 'today', meal_index: 0 })
      )
    })
  })

  it('closes modal when clicking Descartar', async () => {
    await openModal()
    fireEvent.click(screen.getByText('Descartar'))
    await waitFor(() => {
      expect(screen.queryByText('Alternativa sugerida')).not.toBeInTheDocument()
    })
  })

  it('closes modal when clicking the X button', async () => {
    await openModal()
    // Multiple "Cerrar" buttons may exist; pick the one inside the modal dialog
    const closeButtons = screen.getAllByLabelText('Cerrar')
    fireEvent.click(closeButtons[closeButtons.length - 1])
    await waitFor(() => {
      expect(screen.queryByText('Alternativa sugerida')).not.toBeInTheDocument()
    })
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProgressModule from './ProgressModule'
import { progressAPI } from '../services/api'

// Mock the API
jest.mock('../services/api', () => ({
  progressAPI: {
    getEvaluation: jest.fn(),
    getTimeline: jest.fn(),
  },
}))

describe('ProgressModule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    // Mock API to never resolve
    ;(progressAPI.getEvaluation as jest.Mock).mockImplementation(() => new Promise(() => {}))
    ;(progressAPI.getTimeline as jest.Mock).mockImplementation(() => new Promise(() => {}))

    render(<ProgressModule />)
    
    expect(screen.getByText('Cargando progreso...')).toBeInTheDocument()
  })

  it('renders evaluation data when loaded', async () => {
    const mockEvaluation = {
      score: 75,
      estado: 'excelente',
      resumen: 'Excelente progreso en el último mes.',
      metricas: {
        peso_inicial_kg: 82.0,
        peso_actual_kg: 80.0,
        delta_peso_kg: -2.0,
      },
      periodo_usado: 'mes',
      advertencias: [],
    }

    const mockTimeline = {
      periodo: 'mes',
      rango_inicio: '2026-01-22',
      rango_fin: '2026-02-22',
      series: {
        peso: [
          { fecha: '2026-02-01T10:00:00Z', valor: 82.0 },
          { fecha: '2026-02-15T10:00:00Z', valor: 80.0 },
        ],
        porcentaje_grasa: [],
        porcentaje_masa_magra: [],
        calorias_diarias: [],
        macros_porcentaje: [],
      },
      resumen: {
        calorias_semana_real: 14250,
        calorias_semana_meta: 14000,
      },
      advertencias: [],
    }

    ;(progressAPI.getEvaluation as jest.Mock).mockResolvedValue(mockEvaluation)
    ;(progressAPI.getTimeline as jest.Mock).mockResolvedValue(mockTimeline)

    render(<ProgressModule />)

    await waitFor(() => {
      expect(screen.getByText('Evaluación de Progreso')).toBeInTheDocument()
    })

    expect(screen.getByText('Excelente')).toBeInTheDocument()
    expect(screen.getByText('Excelente progreso en el último mes.')).toBeInTheDocument()
  })

  it('renders error state when API fails', async () => {
    ;(progressAPI.getEvaluation as jest.Mock).mockRejectedValue(new Error('API Error'))
    ;(progressAPI.getTimeline as jest.Mock).mockRejectedValue(new Error('API Error'))

    render(<ProgressModule />)

    await waitFor(() => {
      expect(screen.getByText('No se pudo cargar la información de progreso.')).toBeInTheDocument()
    })
  })

  it('displays period selector buttons', async () => {
    const mockEvaluation = {
      score: 50,
      estado: 'muy_bien',
      resumen: 'Buen progreso.',
      metricas: {},
      periodo_usado: 'mes',
      advertencias: [],
    }

    const mockTimeline = {
      periodo: 'mes',
      rango_inicio: '2026-01-22',
      rango_fin: '2026-02-22',
      series: {
        peso: [],
        porcentaje_grasa: [],
        porcentaje_masa_magra: [],
        calorias_diarios: [],
        macros_porcentaje: [],
      },
      resumen: {
        calorias_semana_real: 14000,
        calorias_semana_meta: 14000,
      },
      advertencias: [],
    }

    ;(progressAPI.getEvaluation as jest.Mock).mockResolvedValue(mockEvaluation)
    ;(progressAPI.getTimeline as jest.Mock).mockResolvedValue(mockTimeline)

    render(<ProgressModule />)

    await waitFor(() => {
      expect(screen.getByText('Semana')).toBeInTheDocument()
      expect(screen.getByText('Mes')).toBeInTheDocument()
      expect(screen.getByText('Año')).toBeInTheDocument()
    })
  })
})


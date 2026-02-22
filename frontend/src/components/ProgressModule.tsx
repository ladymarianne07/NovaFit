import React, { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown, Minus, Award, AlertCircle } from 'lucide-react'
import { progressAPI, ProgressEvaluationResponse, ProgressTimelineResponse } from '../services/api'

interface ProgressModuleProps {
  className?: string
}

type Period = 'semana' | 'mes' | 'anio'

const ProgressModule: React.FC<ProgressModuleProps> = ({ className = '' }) => {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [periodo, setPeriodo] = useState<Period>('mes')
  const [evaluation, setEvaluation] = useState<ProgressEvaluationResponse | null>(null)
  const [timeline, setTimeline] = useState<ProgressTimelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProgressData()
  }, [periodo])

  const loadProgressData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [evalData, timelineData] = await Promise.all([
        progressAPI.getEvaluation(periodo),
        progressAPI.getTimeline(periodo)
      ])
      
      setEvaluation(evalData)
      setTimeline(timelineData)
    } catch (err) {
      console.error('Error loading progress data:', err)
      setError('No se pudo cargar la información de progreso.')
    } finally {
      setLoading(false)
    }
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % 2)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + 2) % 2)
  }

  const getScoreBadge = (score: number) => {
    if (score > 70) return { label: 'Excelente', color: 'success', icon: Award }
    if (score > 40) return { label: 'Muy Bien', color: 'info', icon: TrendingUp }
    if (score > 10) return { label: 'En Progreso', color: 'primary', icon: TrendingUp }
    if (score > -10) return { label: 'Estable', color: 'secondary', icon: Minus }
    if (score > -40) return { label: 'Atención', color: 'warning', icon: TrendingDown }
    return { label: 'Revisar Plan', color: 'danger', icon: AlertCircle }
  }

  const formatMetric = (value?: number, suffix: string = '') => {
    if (value === undefined || value === null) return '-'
    return `${value.toFixed(1)}${suffix}`
  }

  const getScorePercentage = (score: number) => {
    // Convert score from [-100, 100] to [0, 100]
    return ((score + 100) / 2)
  }

  // Slide 1: Evaluación de Progreso
  const renderEvaluationSlide = () => {
    if (!evaluation) return null

    const badge = getScoreBadge(evaluation.score)
    const BadgeIcon = badge.icon
    const scorePercentage = getScorePercentage(evaluation.score)

    return (
      <div className="progress-slide">
        <div className="progress-slide-header">
          <h3 className="progress-slide-title">Evaluación de Progreso</h3>
          <p className="progress-slide-subtitle">Período: {periodo}</p>
        </div>

        <div className="progress-score-card">
          <div className={`progress-score-badge progress-score-badge-${badge.color}`}>
            <BadgeIcon size={24} />
            <span className="progress-score-label">{badge.label}</span>
          </div>

          <div className="progress-score-bar-container">
            <div 
              className={`progress-score-bar progress-score-bar-${badge.color}`}
              style={{ width: `${scorePercentage}%` }}
            />
          </div>

          <p className="progress-score-value">
            Score: <strong>{evaluation.score}</strong> / 100
          </p>
        </div>

        <div className="progress-summary">
          <p>{evaluation.resumen}</p>
        </div>

        {evaluation.metricas && (
          <div className="progress-metrics-grid">
            {evaluation.metricas.peso_inicial_kg !== undefined && (
              <div className="progress-metric-item">
                <span className="progress-metric-label">Peso</span>
                <span className="progress-metric-value">
                  {formatMetric(evaluation.metricas.peso_inicial_kg, ' kg')}
                  {' → '}
                  {formatMetric(evaluation.metricas.peso_actual_kg, ' kg')}
                </span>
                <span className={`progress-metric-delta ${(evaluation.metricas.delta_peso_kg ?? 0) < 0 ? 'negative' : 'positive'}`}>
                  {formatMetric(evaluation.metricas.delta_peso_kg, ' kg')}
                </span>
              </div>
            )}

            {evaluation.metricas.porcentaje_grasa_inicial !== undefined && (
              <div className="progress-metric-item">
                <span className="progress-metric-label">Grasa</span>
                <span className="progress-metric-value">
                  {formatMetric(evaluation.metricas.porcentaje_grasa_inicial, '%')}
                  {' → '}
                  {formatMetric(evaluation.metricas.porcentaje_grasa_actual, '%')}
                </span>
                <span className={`progress-metric-delta ${(evaluation.metricas.delta_grasa_pct ?? 0) < 0 ? 'negative' : 'positive'}`}>
                  {formatMetric(evaluation.metricas.delta_grasa_pct, '%')}
                </span>
              </div>
            )}

            {evaluation.metricas.porcentaje_magra_inicial !== undefined && (
              <div className="progress-metric-item">
                <span className="progress-metric-label">Masa Magra</span>
                <span className="progress-metric-value">
                  {formatMetric(evaluation.metricas.porcentaje_magra_inicial, '%')}
                  {' → '}
                  {formatMetric(evaluation.metricas.porcentaje_magra_actual, '%')}
                </span>
                <span className={`progress-metric-delta ${(evaluation.metricas.delta_magra_pct ?? 0) > 0 ? 'positive' : 'negative'}`}>
                  {formatMetric(evaluation.metricas.delta_magra_pct, '%')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  // Slide 2: Evolución Corporal con Gráficos de Línea
  const renderWeightChartSlide = () => {
    if (!timeline || !timeline.series) return null

    const weightData = timeline.series.peso
    const fatData = timeline.series.porcentaje_grasa
    const leanData = timeline.series.porcentaje_masa_magra

    if (weightData.length === 0 && fatData.length === 0 && leanData.length === 0) {
      return (
        <div className="progress-slide">
          <div className="progress-slide-header">
            <h3 className="progress-slide-title">Evolución Corporal</h3>
          </div>
          <div className="progress-empty-state">
            <p>No hay datos de peso o composición corporal para este período.</p>
            <p className="text-sm">Registra mediciones de pliegues cutáneos para ver tu evolución.</p>
          </div>
        </div>
      )
    }

    const renderLineChart = (data: any[], color: string, label: string, maxVal: number = 100) => {
      if (data.length === 0) return null

      const chartWidth = 280
      const chartHeight = 100
      const padding = 30
      const innerWidth = chartWidth - padding * 2
      const innerHeight = chartHeight - padding * 2

      const minVal = Math.min(...data.map(p => p.valor))
      const max = Math.max(maxVal, ...data.map(p => p.valor))
      const range = max - minVal || 1

      const points = data.map((point, idx) => {
        const x = (idx / Math.max(data.length - 1, 1)) * innerWidth + padding
        const y = chartHeight - ((point.valor - minVal) / range) * innerHeight - padding
        return { x, y, ...point }
      })

      const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

      return (
        <div key={label} className="progress-line-chart-container">
          <h4 className="progress-chart-label">{label}</h4>
          <svg width={chartWidth} height={chartHeight} className="progress-line-chart">
            <defs>
              <linearGradient id={`grad-${label}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                <stop offset="100%" stopColor={color} stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={pathD} stroke={color} strokeWidth="2" fill="none" />
            <path d={`${pathD} L ${points[points.length - 1].x} ${chartHeight - padding} L ${points[0].x} ${chartHeight - padding} Z`} 
                  fill={`url(#grad-${label})`} />
            {points.map((p, idx) => (
              <g key={idx}>
                <circle cx={p.x} cy={p.y} r="3" fill={color} />
              </g>
            ))}
          </svg>
          <div className="progress-chart-info">
            {data.length > 0 && (
              <>
                <span className="info-item">Inicio: {data[0].valor.toFixed(1)}</span>
                <span className="info-item">Actual: {data[data.length - 1].valor.toFixed(1)}</span>
                <span className="info-item">Fecha: {new Date(data[data.length - 1].fecha).toLocaleDateString('es', { day: 'numeric', month: 'short' })}</span>
              </>
            )}
          </div>
        </div>
      )
    }

    return (
      <div className="progress-slide">
        <div className="progress-slide-header">
          <h3 className="progress-slide-title">Evolución Corporal</h3>
        </div>

        <div className="progress-evolution-grid">
          {renderLineChart(weightData, '#60a5fa', 'Peso (kg)', 120)}
          {renderLineChart(fatData, '#f87171', 'Grasa Corporal (%)', 50)}
          {renderLineChart(leanData, '#34d399', 'Masa Magra (%)', 50)}
        </div>
      </div>
    )
  }



  if (loading) {
    return (
      <div className={`progress-module ${className}`}>
        <div className="progress-loading">
          <div className="loading-stack">
            <div className="neon-loader neon-loader--lg" aria-hidden="true"></div>
            <p>Cargando progreso...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`progress-module ${className}`}>
        <div className="progress-error">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <p>{error}</p>
          <button onClick={loadProgressData} className="progress-retry-button">
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`progress-module ${className}`}>
      <div className="progress-period-selector">
        <button
          className={`progress-period-button ${periodo === 'semana' ? 'active' : ''}`}
          onClick={() => setPeriodo('semana')}
        >
          Semana
        </button>
        <button
          className={`progress-period-button ${periodo === 'mes' ? 'active' : ''}`}
          onClick={() => setPeriodo('mes')}
        >
          Mes
        </button>
        <button
          className={`progress-period-button ${periodo === 'anio' ? 'active' : ''}`}
          onClick={() => setPeriodo('anio')}
        >
          Año
        </button>
      </div>

      <div className="progress-slides-container">
        <div className="progress-slides-wrapper" style={{ transform: `translateX(calc(-${currentSlide} * 100%))` }}>
          <div className="progress-slide-item">
            {renderEvaluationSlide()}
          </div>
          <div className="progress-slide-item">
            {renderWeightChartSlide()}
          </div>
        </div>
      </div>

      <div className="progress-navigation">
        <button
          onClick={prevSlide}
          className="progress-nav-button"
          disabled={currentSlide === 0}
        >
          <ChevronLeft size={20} />
        </button>

        <div className="progress-dots">
          {[0, 1].map((idx) => (
            <button
              key={idx}
              className={`progress-dot ${currentSlide === idx ? 'active' : ''}`}
              onClick={() => setCurrentSlide(idx)}
            />
          ))}
        </div>

        <button
          onClick={nextSlide}
          className="progress-nav-button"
          disabled={currentSlide === 1}
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  )
}

export default ProgressModule

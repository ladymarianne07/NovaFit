/**
 * RoutineLogModal — lets the user log a completed routine session,
 * deselecting any exercises they skipped, with live calorie preview.
 */
import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { RoutineSession, RoutineLogSessionRequest, routineAPI, WorkoutSessionResponse } from '../services/api'

interface RoutineLogModalProps {
  isOpen: boolean
  sessions: RoutineSession[]
  onClose: () => void
  onLogged: (session: WorkoutSessionResponse) => void
}

const today = (): string => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const RoutineLogModal: React.FC<RoutineLogModalProps> = ({ isOpen, sessions, onClose, onLogged }) => {
  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [skippedIds, setSkippedIds] = useState<Set<string>>(new Set())
  const [sessionDate, setSessionDate] = useState<string>(today())
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen && sessions.length > 0) {
      setSelectedSessionId(sessions[0].id)
      setSkippedIds(new Set())
      setSessionDate(today())
      setError('')
    }
  }, [isOpen, sessions])

  useEffect(() => {
    setSkippedIds(new Set())
  }, [selectedSessionId])

  useEffect(() => {
    if (!isOpen) return
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape' && isOpen) onClose() }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  const activeSession = sessions.find((s) => s.id === selectedSessionId) ?? null

  const calcCalories = (): number => {
    if (!activeSession) return 0
    const skipped = activeSession.exercises
      .filter((ex) => skippedIds.has(ex.id))
      .reduce((acc, ex) => acc + ex.estimated_calories, 0)
    return Math.round(activeSession.estimated_calories_per_session - skipped)
  }

  const toggleSkipped = (exerciseId: string) => {
    setSkippedIds((prev) => {
      const next = new Set(prev)
      if (next.has(exerciseId)) next.delete(exerciseId)
      else next.add(exerciseId)
      return next
    })
  }

  const handleConfirm = async () => {
    if (!activeSession || !sessionDate) return
    setIsSubmitting(true)
    setError('')
    try {
      const payload: RoutineLogSessionRequest = {
        session_id: activeSession.id,
        session_date: sessionDate,
        skipped_exercise_ids: Array.from(skippedIds),
      }
      const result = await routineAPI.logSession(payload)
      window.dispatchEvent(new Event('workout:updated'))
      onLogged(result)
      onClose()
    } catch {
      setError('No se pudo guardar el entrenamiento. Intentá de nuevo.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div className="ai-confirm-overlay" onClick={onClose}>
      <div
        className="ai-confirm-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="routine-log-title"
      >
        {/* Header */}
        <div className="ai-confirm-header">
          <h3 id="routine-log-title" className="ai-confirm-title">
            Registrar entrenamiento
          </h3>
          <button type="button" className="ai-confirm-close-btn" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="ai-confirm-body">
          <div className="ai-confirm-modal">

            {/* Session selector */}
            <div className="routine-log-field">
              <label className="routine-log-label">Sesión</label>
              <select
                className="routine-log-select"
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.day_label || `${s.label} — ${s.title}`}
                  </option>
                ))}
              </select>
            </div>

            {/* Date */}
            <div className="routine-log-field">
              <label className="routine-log-label">Fecha</label>
              <input
                type="date"
                className="routine-log-input"
                value={sessionDate}
                onChange={(e) => setSessionDate(e.target.value)}
              />
            </div>

            {/* Exercise checklist */}
            {activeSession && (
              <div className="routine-log-exercises">
                <p className="routine-log-section-title">
                  Marcá los ejercicios que <strong>no</strong> hiciste
                </p>
                {activeSession.exercises.map((ex) => {
                  const skipped = skippedIds.has(ex.id)
                  return (
                    <label
                      key={ex.id}
                      className={`routine-log-exercise-row${skipped ? ' skipped' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={skipped}
                        onChange={() => toggleSkipped(ex.id)}
                        className="routine-log-checkbox"
                      />
                      <span className="routine-log-exercise-name">{ex.name}</span>
                      <span className="routine-log-exercise-cal">
                        {skipped ? (
                          <span className="routine-log-cal-skipped">−{Math.round(ex.estimated_calories)} kcal</span>
                        ) : (
                          <span>{Math.round(ex.estimated_calories)} kcal</span>
                        )}
                      </span>
                    </label>
                  )
                })}
              </div>
            )}

            {/* Calorie summary */}
            <div className="routine-log-summary">
              <span className="routine-log-summary-label">Total estimado</span>
              <span className="routine-log-summary-value">{calcCalories()} kcal</span>
            </div>

            {error && <p className="routine-log-error">{error}</p>}

            {/* Actions */}
            <div className="ai-confirm-actions">
              <button
                type="button"
                className="nutrition-secondary-button"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="nutrition-primary-button"
                onClick={handleConfirm}
                disabled={isSubmitting || !activeSession}
              >
                {isSubmitting ? 'Guardando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}

export default RoutineLogModal

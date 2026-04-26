/**
 * RoutineLogModal — two-step flow to log a completed routine session.
 *
 * Step 1 — "¿Completaste tu rutina de hoy?" + session selector.
 * Step 2 — Adjust: mark skipped exercises + add extra exercises on top.
 *
 * Calories:
 *   - Base: MET × weight × hours (calculated server-side, not shown as exact preview)
 *   - Skipped: proportionally removed
 *   - Extras: per-type MET × weight × duration (server-side)
 *   - Frontend shows an indicative preview using the AI estimate as proxy.
 */
import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Trash2 } from 'lucide-react'
import {
  ExtraExercise,
  ExtraExerciseType,
  RoutineLogSessionRequest,
  RoutineSession,
  WorkoutSessionResponse,
  routineAPI,
} from '../services/api'

// ── Constants ─────────────────────────────────────────────────────────────────

const EXTRA_TYPE_OPTIONS: Array<{ value: ExtraExerciseType; label: string; met: number }> = [
  { value: 'resistance', label: 'Ejercicio con peso', met: 4.5 },
  { value: 'cardio_moderate', label: 'Cardio moderado', met: 7.0 },
  { value: 'cardio_high', label: 'Cardio intenso', met: 9.5 },
  { value: 'hiit', label: 'HIIT', met: 8.5 },
  { value: 'yoga', label: 'Yoga / Flexibilidad', met: 2.5 },
  { value: 'walking', label: 'Caminata', met: 3.5 },
]

// ── Types ─────────────────────────────────────────────────────────────────────

interface RoutineLogModalProps {
  isOpen: boolean
  sessions: RoutineSession[]
  onClose: () => void
  onLogged: (session: WorkoutSessionResponse) => void
}

type Step = 'confirm' | 'adjust'

interface ExtraRow {
  id: string
  name: string
  duration_minutes: number
  exercise_type: ExtraExerciseType
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const todayStr = (): string => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

let _nextId = 0
const uid = () => String(++_nextId)

// ── Component ─────────────────────────────────────────────────────────────────

const RoutineLogModal: React.FC<RoutineLogModalProps> = ({ isOpen, sessions, onClose, onLogged }) => {
  const [step, setStep] = useState<Step>('confirm')
  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [sessionDate, setSessionDate] = useState<string>(todayStr())
  const [skippedIds, setSkippedIds] = useState<Set<string>>(new Set())
  const [extras, setExtras] = useState<ExtraRow[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Reset on open
  useEffect(() => {
    if (isOpen && sessions.length > 0) {
      setStep('confirm')
      setSelectedSessionId(sessions[0].id)
      setSessionDate(todayStr())
      setSkippedIds(new Set())
      setExtras([])
      setError('')
    }
  }, [isOpen, sessions])

  // Clear skips when session changes
  useEffect(() => { setSkippedIds(new Set()) }, [selectedSessionId])

  // Body scroll lock
  useEffect(() => {
    if (!isOpen) return
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  // Escape key
  useEffect(() => {
    const fn = (e: KeyboardEvent) => { if (e.key === 'Escape' && isOpen) onClose() }
    document.addEventListener('keydown', fn)
    return () => document.removeEventListener('keydown', fn)
  }, [isOpen, onClose])

  const activeSession = sessions.find((s) => s.id === selectedSessionId) ?? null

  // ── Calorie preview — MET-based estimate (mirrors backend logic) ──
  // Base: fuerza_general MET (5.0) × 70 kg placeholder × session duration, scaled for skips.
  // Extras: their own MET × 70 kg × hours. Backend recalculates with real weight on submit.

  const previewCalories = (): number => {
    if (!activeSession) return 0
    const exercises = activeSession.exercises
    const n = exercises.length
    const done = n - exercises.filter((ex) => skippedIds.has(ex.id)).length
    const scale = n > 0 ? done / n : 1
    const durationMinutes = activeSession.session_duration_minutes ?? 60
    const base = Math.round(5.0 * 70 * (durationMinutes / 60) * scale)

    const extraKcal = extras.reduce((acc, row) => {
      const opt = EXTRA_TYPE_OPTIONS.find((o) => o.value === row.exercise_type)
      const met = opt?.met ?? 4.5
      return acc + Math.round(met * 70 * (row.duration_minutes / 60))
    }, 0)

    return base + extraKcal
  }

  // ── Extras helpers ────────────────────────────────────────────────────────

  const addExtra = () => {
    setExtras((prev) => [
      ...prev,
      { id: uid(), name: '', duration_minutes: 20, exercise_type: 'resistance' },
    ])
  }

  const updateExtra = <K extends keyof ExtraRow>(id: string, field: K, value: ExtraRow[K]) => {
    setExtras((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: value } : r)))
  }

  const removeExtra = (id: string) => {
    setExtras((prev) => prev.filter((r) => r.id !== id))
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  const handleConfirm = async () => {
    if (!activeSession || !sessionDate) return
    setIsSubmitting(true)
    setError('')
    try {
      const extraExercises: ExtraExercise[] = extras
        .filter((r) => r.name.trim().length > 0 && r.duration_minutes > 0)
        .map((r) => ({
          name: r.name.trim(),
          duration_minutes: r.duration_minutes,
          exercise_type: r.exercise_type,
        }))

      const payload: RoutineLogSessionRequest = {
        session_id: activeSession.id,
        session_date: sessionDate,
        skipped_exercise_ids: Array.from(skippedIds),
        extra_exercises: extraExercises,
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
            {step === 'confirm' ? 'Registrar entrenamiento' : 'Ajustar sesión'}
          </h3>
          <button type="button" className="ai-confirm-close-btn" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="ai-confirm-body">
          <div className="ai-confirm-modal">

            {/* ── STEP 1: confirm ── */}
            {step === 'confirm' && (
              <>
                {/* Session selector */}
                <div className="routine-log-field">
                  <label className="routine-log-label">Sesión de hoy</label>
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

                {/* Question */}
                <p className="routine-log-question">
                  ¿Completaste la rutina normal?
                </p>

                <div className="routine-log-confirm-actions">
                  <button
                    type="button"
                    className="routine-log-confirm-btn yes"
                    onClick={handleConfirm}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Guardando...' : 'Sí, la completé'}
                  </button>
                  <button
                    type="button"
                    className="routine-log-confirm-btn adjust"
                    onClick={() => setStep('adjust')}
                    disabled={isSubmitting}
                  >
                    Ajustar sesión
                  </button>
                </div>

                {error && <p className="routine-log-error">{error}</p>}
              </>
            )}

            {/* ── STEP 2: adjust ── */}
            {step === 'adjust' && activeSession && (
              <>
                {/* Skipped exercises */}
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
                          onChange={() => {
                            setSkippedIds((prev) => {
                              const next = new Set(prev)
                              if (next.has(ex.id)) next.delete(ex.id)
                              else next.add(ex.id)
                              return next
                            })
                          }}
                          className="routine-log-checkbox"
                        />
                        <span className="routine-log-exercise-name">{ex.name}</span>
                      </label>
                    )
                  })}
                </div>

                {/* Extra exercises */}
                <div className="routine-log-extras">
                  <p className="routine-log-section-title">Ejercicios extras</p>

                  {extras.map((row) => (
                    <div key={row.id} className="routine-log-extra-row">
                      <input
                        type="text"
                        className="routine-log-extra-name"
                        placeholder="Nombre del ejercicio"
                        value={row.name}
                        onChange={(e) => updateExtra(row.id, 'name', e.target.value)}
                      />
                      <div className="routine-log-extra-controls">
                        <select
                          className="routine-log-extra-type"
                          value={row.exercise_type}
                          onChange={(e) =>
                            updateExtra(row.id, 'exercise_type', e.target.value as ExtraExerciseType)
                          }
                        >
                          {EXTRA_TYPE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                        <div className="routine-log-extra-duration">
                          <input
                            type="number"
                            className="routine-log-extra-duration-input"
                            min={1}
                            max={180}
                            value={row.duration_minutes}
                            onChange={(e) =>
                              updateExtra(row.id, 'duration_minutes', Math.max(1, Number(e.target.value)))
                            }
                          />
                          <span className="routine-log-extra-unit">min</span>
                        </div>
                        <button
                          type="button"
                          className="routine-log-extra-remove"
                          onClick={() => removeExtra(row.id)}
                          aria-label="Eliminar ejercicio extra"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}

                  <button
                    type="button"
                    className="routine-log-add-extra-btn"
                    onClick={addExtra}
                  >
                    <Plus size={14} />
                    Agregar ejercicio extra
                  </button>
                </div>

                {/* Calorie preview */}
                <div className="routine-log-summary">
                  <span className="routine-log-summary-label">Estimado de calorías</span>
                  <span className="routine-log-summary-value">
                    ~{previewCalories()} kcal
                  </span>
                </div>
                <p className="routine-log-summary-hint">
                  El valor exacto se calcula con tu peso al guardar.
                </p>

                {error && <p className="routine-log-error">{error}</p>}

                {/* Actions */}
                <div className="ai-confirm-actions">
                  <button
                    type="button"
                    className="nutrition-secondary-button"
                    onClick={() => setStep('confirm')}
                    disabled={isSubmitting}
                  >
                    Volver
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
              </>
            )}

          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default RoutineLogModal

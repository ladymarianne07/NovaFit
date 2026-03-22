/**
 * RoutineModule — Create, view, and manage the user's personalized workout routine.
 *
 * Creation modes:
 *   1. Upload a file (PDF / image / text) → parsed by Gemini
 *   2. AI generation via intake form + free text → personal trainer prompt
 *
 * Viewing features:
 *   - Sessions grid with calorie estimates
 *   - Full HTML viewer (iframe with 3-theme switcher built in)
 *   - Edit mode: describe changes → AI updates the routine
 *   - Log session: register a completed session
 */
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Dumbbell,
  FileUp,
  Pencil,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  X,
} from 'lucide-react'
// Plus kept for the "Crear / Reemplazar" trigger button
import {
  RoutineEditRequest,
  RoutineGenerateRequest,
  RoutineIntakeData,
  UserRoutineResponse,
  routineAPI,
} from '../services/api'

// ── Types ────────────────────────────────────────────────────────────────────

interface RoutineModuleProps {
  className?: string
}

type CreateMode = 'ai' | 'file'

const ACCEPTED_MIME_TYPES = 'text/plain,application/pdf,image/jpeg,image/png,image/webp'

const OBJECTIVE_OPTIONS = [
  { value: 'fat_loss', label: 'Pérdida de grasa / definición' },
  { value: 'body_recomp', label: 'Recomposición corporal' },
  { value: 'muscle_gain', label: 'Ganancia muscular' },
] as const

const FREQUENCY_OPTIONS = [
  { value: '2', label: '2 días por semana' },
  { value: '3-4', label: '3-4 días por semana' },
  { value: '5+', label: '5 o más días por semana' },
] as const

const EXPERIENCE_OPTIONS = [
  { value: 'principiante', label: 'Principiante (< 1 año)' },
  { value: 'intermedio', label: 'Intermedio (1-3 años)' },
  { value: 'avanzado', label: 'Avanzado (3+ años)' },
] as const

const EQUIPMENT_OPTIONS = [
  { value: 'gimnasio completo', label: 'Gimnasio completo' },
  { value: 'mancuernas en casa', label: 'Mancuernas en casa' },
  { value: 'bandas elásticas', label: 'Bandas elásticas' },
  { value: 'peso corporal', label: 'Sólo peso corporal' },
] as const

const DEFAULT_INTAKE: RoutineIntakeData = {
  objective: 'body_recomp',
  duration_months: 1,
  health_conditions: '',
  medications: '',
  injuries: '',
  preferred_exercises: '',
  frequency_days: '3-4',
  experience_level: 'principiante',
  equipment: 'gimnasio completo',
  session_duration_minutes: 60,
}

// Required fields that trigger the missing-data modal
const REQUIRED_FIELDS: Array<keyof RoutineIntakeData> = [
  'objective',
  'duration_months',
  'health_conditions',
  'injuries',
]

// ── Component ─────────────────────────────────────────────────────────────────

const RoutineModule: React.FC<RoutineModuleProps> = ({ className }) => {
  // Global state
  const [routine, setRoutine] = useState<UserRoutineResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Creation state
  const [createMode, setCreateMode] = useState<CreateMode>('ai')
  const [intake, setIntake] = useState<RoutineIntakeData>(DEFAULT_INTAKE)
  const [freeText, setFreeText] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [createError, setCreateError] = useState('')

  // File upload state
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Missing-data modal
  const [showMissingModal, setShowMissingModal] = useState(false)
  const [missingFields, setMissingFields] = useState<string[]>([])

  // Edit mode
  const [showEditBar, setShowEditBar] = useState(false)
  const [editInstruction, setEditInstruction] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [editError, setEditError] = useState('')

  // Viewer modal
  const [showHtmlModal, setShowHtmlModal] = useState(false)

  // ── Load routine on mount ─────────────────────────────────────────────────

  const loadRoutine = useCallback(async () => {
    try {
      const data = await routineAPI.getActive()
      setRoutine(data)
      if (data.status === 'ready') setTopTab('view')
    } catch {
      // No active routine yet
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadRoutine() }, [loadRoutine])

  // ── Create modal helpers ──────────────────────────────────────────────────

  const openCreateModal = () => {
    setCreateError('')
    setCreateMode('ai')
    setShowCreateModal(true)
  }

  const closeCreateModal = () => {
    setShowCreateModal(false)
    setCreateError('')
    setFreeText('')
    setIntake(DEFAULT_INTAKE)
  }

  // ── Intake helpers ────────────────────────────────────────────────────────

  const updateIntake = <K extends keyof RoutineIntakeData>(
    field: K,
    value: RoutineIntakeData[K],
  ) => setIntake((prev) => ({ ...prev, [field]: value }))

  const getMissingRequired = (): string[] => {
    const labels: Record<string, string> = {
      objective: 'Objetivo principal',
      duration_months: 'Duración en meses',
      health_conditions: 'Condiciones de salud',
      injuries: 'Lesiones actuales o recientes',
    }
    return REQUIRED_FIELDS.filter((f) => {
      const v = intake[f]
      return v === '' || v === null || v === undefined || v === 0
    }).map((f) => labels[f] ?? f)
  }

  // ── Generate from text ────────────────────────────────────────────────────

  const handleGenerate = () => {
    setCreateError('')
    const missing = getMissingRequired()
    if (missing.length > 0) {
      setMissingFields(missing)
      setShowMissingModal(true)
      return
    }
    executeGenerate()
  }

  const executeGenerate = async () => {
    setShowMissingModal(false)
    setIsGenerating(true)
    setCreateError('')
    try {
      const payload: RoutineGenerateRequest = { intake, free_text: freeText }
      const data = await routineAPI.generateFromText(payload)
      setRoutine(data)
      if (data.status === 'ready') {
        closeCreateModal()
      } else if (data.status === 'error') {
        setCreateError(data.error_message || 'Error al generar la rutina.')
      }
    } catch (err: unknown) {
      setCreateError(
        err instanceof Error ? err.message : 'No se pudo generar la rutina. Intentá de nuevo.',
      )
    } finally {
      setIsGenerating(false)
    }
  }

  // ── File upload ───────────────────────────────────────────────────────────

  const handleFile = async (file: File) => {
    setCreateError('')
    setIsUploading(true)
    try {
      const data = await routineAPI.upload(file)
      setRoutine(data)
      if (data.status === 'ready') closeCreateModal()
      else if (data.status === 'error') setCreateError(data.error_message || 'Error al procesar el archivo.')
    } catch (err: unknown) {
      setCreateError(
        err instanceof Error ? err.message : 'No se pudo procesar el archivo. Intentá de nuevo.',
      )
    } finally {
      setIsUploading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  // ── Edit routine ──────────────────────────────────────────────────────────

  const handleEdit = async () => {
    if (!editInstruction.trim() || editInstruction.trim().length < 5) return
    setEditError('')
    setIsEditing(true)
    try {
      const payload: RoutineEditRequest = { edit_instruction: editInstruction.trim() }
      const data = await routineAPI.editRoutine(payload)
      setRoutine(data)
      if (data.status === 'ready') {
        setShowEditBar(false)
        setEditInstruction('')
      } else if (data.status === 'error') {
        setEditError(data.error_message || 'Error al editar la rutina.')
      }
    } catch (err: unknown) {
      setEditError(
        err instanceof Error ? err.message : 'No se pudo editar la rutina. Intentá de nuevo.',
      )
    } finally {
      setIsEditing(false)
    }
  }

  const sessions = routine?.routine_data?.sessions ?? []
  const hasActiveRoutine = routine?.status === 'ready'

  // ── Loading ───────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className={`routine-module ${className ?? ''}`}>
        <div className="routine-loading">
          <div className="neon-loader neon-loader--md" aria-hidden="true" />
          <p>Cargando rutina...</p>
        </div>
      </div>
    )
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className={`routine-module ${className ?? ''}`}>
      {/* ══════════════ VIEW ══════════════ */}
      {!hasActiveRoutine ? (
        <div className="routine-empty-state">
          <Dumbbell size={40} className="routine-empty-icon" />
          <p className="routine-empty-title">Todavía no tenés una rutina</p>
          <p className="routine-empty-sub">
            Creá una con IA o subí tu rutina existente para comenzar.
          </p>
          <button
            type="button"
            className="routine-primary-btn"
            onClick={openCreateModal}
          >
            <Sparkles size={16} />
            Crear mi rutina
          </button>
        </div>
      ) : (
        <>
          {/* ── Header card ── */}
          <div className="routine-ready-card">
            <div className="routine-ready-top">
              <div className="routine-ready-meta">
                <h2 className="routine-ready-title">
                  {routine?.routine_data?.title ?? 'Mi Rutina'}
                </h2>
                {routine?.routine_data?.subtitle && (
                  <p className="routine-ready-subtitle">{routine.routine_data.subtitle}</p>
                )}
              </div>
              <span className={`routine-source-badge ${routine?.source_type === 'ai_text' ? 'ai' : 'file'}`}>
                {routine?.source_type === 'ai_text' ? '✨ Generada con IA' : '📄 Subida'}
              </span>
            </div>

            <button
              type="button"
              className="routine-primary-btn"
              onClick={() => setShowHtmlModal(true)}
            >
              Ver rutina completa
            </button>

            <div className="routine-ready-actions">
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={openCreateModal}
              >
                <Plus size={14} />
                Reemplazar
              </button>
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={() => { setShowEditBar(!showEditBar); setEditError('') }}
                aria-pressed={showEditBar}
              >
                <Pencil size={14} />
                Pedir cambios
              </button>
            </div>
          </div>

          {/* Health analysis warning */}
          {routine?.health_analysis?.warning && (
            <div className="routine-health-warning">
              <span>⚠️</span>
              <p>{routine.health_analysis.warning}</p>
            </div>
          )}

          {/* Edit bar */}
          {showEditBar && (
            <div className="routine-edit-bar">
              <p className="routine-edit-label">
                Describí qué querés cambiar en tu rutina:
              </p>
              <div className="routine-edit-row">
                <textarea
                  className="routine-edit-textarea"
                  placeholder="Ej: Agregá más ejercicios de espalda, sacá el peso muerto, quiero más días de descanso..."
                  value={editInstruction}
                  onChange={(e) => setEditInstruction(e.target.value)}
                  rows={3}
                  disabled={isEditing}
                />
                <button
                  type="button"
                  className="routine-primary-btn routine-edit-send"
                  onClick={handleEdit}
                  disabled={isEditing || editInstruction.trim().length < 5}
                >
                  {isEditing ? (
                    <div className="neon-loader neon-loader--sm" aria-hidden="true" />
                  ) : (
                    <Send size={16} />
                  )}
                  {isEditing ? 'Aplicando...' : 'Aplicar'}
                </button>
              </div>
              {editError && <p className="routine-error">{editError}</p>}
            </div>
          )}

          {/* Sessions section */}
          <div className="routine-sessions-section">
            <p className="routine-sessions-section-label">Semana de entrenamiento</p>
            <div className="routine-sessions-grid">
              {sessions.map((s) => (
                <div key={s.id} className="routine-session-card">
                  <p className="routine-session-label">{s.day_label || s.label}</p>
                  <div className="routine-session-row">
                    <div
                      className="routine-session-dot"
                      style={{ background: s.color ?? '#c8f55a' }}
                    />
                    <p className="routine-session-title">{s.title}</p>
                    <span className="routine-session-cal">
                      {Math.round(s.estimated_calories_per_session)} kcal
                    </span>
                  </div>
                  <p className="routine-session-exercises">
                    {s.exercises?.length ?? 0} ejercicios
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ══════════ CREATE MODAL ══════════ */}
      {showCreateModal && createPortal(
        <div
          className="routine-create-overlay"
          onClick={closeCreateModal}
          role="dialog"
          aria-modal="true"
          aria-label={hasActiveRoutine ? 'Reemplazar rutina' : 'Crear mi rutina'}
        >
          <div
            className="routine-create-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="routine-create-header">
              <span className="routine-create-header-title">
                {hasActiveRoutine ? 'Reemplazar rutina' : 'Crear mi rutina'}
              </span>
              <button
                type="button"
                className="routine-missing-close"
                onClick={closeCreateModal}
                aria-label="Cerrar"
              >
                <X size={18} />
              </button>
            </div>

            {/* Mode selector */}
            <div className="routine-create-modes">
              <button
                className={`routine-mode-btn ${createMode === 'ai' ? 'active' : ''}`}
                onClick={() => { setCreateMode('ai'); setCreateError('') }}
              >
                <Sparkles size={16} />
                Crear con IA
              </button>
              <button
                className={`routine-mode-btn ${createMode === 'file' ? 'active' : ''}`}
                onClick={() => { setCreateMode('file'); setCreateError('') }}
              >
                <FileUp size={16} />
                Subir archivo
              </button>
            </div>

            {/* ── AI creation mode ── */}
            {createMode === 'ai' && (
              <div className="routine-ai-creator">
                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Contanos qué estás buscando <span className="routine-optional">(opcional)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: Quiero una rutina de 3 días para bajar de peso, me gustan las máquinas, tengo poco tiempo en el gym..."
                    value={freeText}
                    onChange={(e) => setFreeText(e.target.value)}
                    rows={3}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-form">
                  <p className="routine-intake-section-title">
                    Información para personalizar tu rutina
                  </p>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Objetivo principal <span className="routine-required">*</span>
                    </label>
                    <div className="routine-objective-grid">
                      {OBJECTIVE_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          className={`routine-objective-btn ${intake.objective === opt.value ? 'active' : ''}`}
                          onClick={() => updateIntake('objective', opt.value)}
                          disabled={isGenerating}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Condiciones de salud, enfermedades o patologías{' '}
                      <span className="routine-required">*</span>
                    </label>
                    <textarea
                      className="routine-intake-textarea"
                      placeholder="Ej: Hernia lumbar L4-L5, hipotiroidismo, artritis en rodilla. Si no tenés ninguna escribí: ninguna"
                      value={intake.health_conditions}
                      onChange={(e) => updateIntake('health_conditions', e.target.value)}
                      rows={2}
                      disabled={isGenerating}
                    />
                  </div>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Medicamentos actuales{' '}
                      <span className="routine-optional">(opcional)</span>
                    </label>
                    <textarea
                      className="routine-intake-textarea"
                      placeholder="Ej: Levotiroxina, metformina. Si no tomás ninguno podés dejarlo vacío."
                      value={intake.medications}
                      onChange={(e) => updateIntake('medications', e.target.value)}
                      rows={2}
                      disabled={isGenerating}
                    />
                  </div>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Lesiones actuales o recientes{' '}
                      <span className="routine-required">*</span>
                    </label>
                    <textarea
                      className="routine-intake-textarea"
                      placeholder="Ej: Esguince de tobillo hace 3 meses, ya recuperado. Dolor crónico en hombro derecho."
                      value={intake.injuries}
                      onChange={(e) => updateIntake('injuries', e.target.value)}
                      rows={2}
                      disabled={isGenerating}
                    />
                  </div>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Tipos de ejercicio que te gustan{' '}
                      <span className="routine-optional">(opcional)</span>
                    </label>
                    <textarea
                      className="routine-intake-textarea"
                      placeholder="Ej: Máquinas, sin peso libre, me gusta el hip thrust, crossfit, funcional..."
                      value={intake.preferred_exercises}
                      onChange={(e) => updateIntake('preferred_exercises', e.target.value)}
                      rows={2}
                      disabled={isGenerating}
                    />
                  </div>

                  <div className="routine-intake-row">
                    <div className="routine-intake-field">
                      <label className="routine-intake-label">Frecuencia</label>
                      <select
                        className="routine-intake-select"
                        value={intake.frequency_days}
                        onChange={(e) => updateIntake('frequency_days', e.target.value as RoutineIntakeData['frequency_days'])}
                        disabled={isGenerating}
                      >
                        {FREQUENCY_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="routine-intake-field">
                      <label className="routine-intake-label">Experiencia</label>
                      <select
                        className="routine-intake-select"
                        value={intake.experience_level}
                        onChange={(e) => updateIntake('experience_level', e.target.value as RoutineIntakeData['experience_level'])}
                        disabled={isGenerating}
                      >
                        {EXPERIENCE_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="routine-intake-row">
                    <div className="routine-intake-field">
                      <label className="routine-intake-label">Equipamiento</label>
                      <select
                        className="routine-intake-select"
                        value={intake.equipment}
                        onChange={(e) => updateIntake('equipment', e.target.value as RoutineIntakeData['equipment'])}
                        disabled={isGenerating}
                      >
                        {EQUIPMENT_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="routine-intake-field">
                      <label className="routine-intake-label">
                        Duración del plan <span className="routine-required">*</span>
                      </label>
                      <div className="routine-intake-number-wrap">
                        <input
                          type="number"
                          className="routine-intake-select"
                          min={1}
                          max={12}
                          value={intake.duration_months}
                          onChange={(e) => updateIntake('duration_months', Number(e.target.value))}
                          disabled={isGenerating}
                        />
                        <span className="routine-intake-unit">meses</span>
                      </div>
                    </div>
                  </div>

                  <div className="routine-intake-field">
                    <label className="routine-intake-label">
                      Duración por sesión: <strong>{intake.session_duration_minutes} min</strong>
                    </label>
                    <input
                      type="range"
                      min={20}
                      max={120}
                      step={5}
                      value={intake.session_duration_minutes}
                      onChange={(e) => updateIntake('session_duration_minutes', Number(e.target.value))}
                      className="routine-intake-range"
                      disabled={isGenerating}
                    />
                    <div className="routine-intake-range-labels">
                      <span>20 min</span>
                      <span>120 min</span>
                    </div>
                  </div>
                </div>

                {createError && <p className="routine-error">{createError}</p>}

                <button
                  type="button"
                  className="routine-primary-btn routine-generate-btn"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <div className="neon-loader neon-loader--sm" aria-hidden="true" />
                      Generando rutina con IA...
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} />
                      Generar mi rutina personalizada
                    </>
                  )}
                </button>
              </div>
            )}

            {/* ── File upload mode ── */}
            {createMode === 'file' && (
              <div className="routine-file-creator">
                <div className="routine-disclaimer">
                  <p className="routine-disclaimer-title">📋 Información requerida en el archivo</p>
                  <p className="routine-disclaimer-text">
                    Para que la IA pueda armar tu rutina correctamente, el archivo debe incluir al menos:
                  </p>
                  <ul className="routine-disclaimer-list">
                    <li>🎯 <strong>Objetivo</strong> (pérdida de grasa, recomposición o ganancia muscular)</li>
                    <li>🔥 <strong>Calentamiento</strong> y movilidad articular</li>
                    <li>💪 <strong>Rutina de ejercicios</strong> organizados por día o bloque</li>
                    <li>📊 <strong>Series y repeticiones</strong> por ejercicio</li>
                    <li>📅 <strong>Cantidad de meses</strong> o fases del plan</li>
                  </ul>
                  <p className="routine-disclaimer-note">
                    ⚠️ Si el archivo no contiene toda la información, la IA intentará inferirla.
                    Podés agregar notas de salud o lesiones en el documento para mayor precisión.
                  </p>
                </div>

                <div
                  className={`routine-dropzone${isDragging ? ' dragging' : ''}`}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click() }}
                  aria-label="Seleccionar archivo de rutina"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_MIME_TYPES}
                    onChange={handleInputChange}
                    className="routine-file-input"
                    aria-hidden="true"
                  />
                  {isUploading ? (
                    <div className="routine-dropzone-content">
                      <div className="neon-loader neon-loader--md" aria-hidden="true" />
                      <p className="routine-dropzone-text">Procesando con IA...</p>
                      <p className="routine-dropzone-hint">Esto puede tardar unos segundos</p>
                    </div>
                  ) : (
                    <div className="routine-dropzone-content">
                      <FileUp size={32} className="routine-dropzone-icon" />
                      <p className="routine-dropzone-text">
                        {isDragging ? 'Soltá el archivo aquí' : 'Arrastrá tu rutina o hacé click para seleccionar'}
                      </p>
                      <p className="routine-dropzone-hint">PDF · Imagen (JPG, PNG) · Texto (.txt)</p>
                    </div>
                  )}
                </div>

                {createError && <p className="routine-error">{createError}</p>}
              </div>
            )}
          </div>
        </div>,
        document.body,
      )}

      {/* ══════════ MISSING DATA MODAL ══════════ */}
      {showMissingModal && createPortal(
        <div
          className="routine-missing-overlay"
          onClick={() => setShowMissingModal(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Datos faltantes"
        >
          <div
            className="routine-missing-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="routine-missing-close"
              onClick={() => setShowMissingModal(false)}
              aria-label="Cerrar"
            >
              <X size={18} />
            </button>

            <p className="routine-missing-title">⚠️ Faltan algunos datos clave</p>
            <p className="routine-missing-sub">
              Para armar la mejor rutina posible necesitamos saber:
            </p>

            <ul className="routine-missing-list">
              {missingFields.map((f) => (
                <li key={f} className="routine-missing-item">
                  <span className="routine-missing-dot" />
                  {f}
                </li>
              ))}
            </ul>

            <p className="routine-missing-hint">
              Podés completarlos arriba o pedirle a la IA que infiera con lo que tiene.
            </p>

            <div className="routine-missing-actions">
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={() => setShowMissingModal(false)}
              >
                Completar datos
              </button>
              <button
                type="button"
                className="routine-primary-btn"
                onClick={executeGenerate}
              >
                <RefreshCw size={15} />
                La IA infiere lo que falta
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )}

      {/* ══════════ HTML VIEWER MODAL ══════════ */}
      {showHtmlModal && routine?.html_content && createPortal(
        <div
          className="routine-html-overlay"
          onClick={() => setShowHtmlModal(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Visualizador de rutina"
        >
          <div
            className="routine-html-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="routine-html-toolbar">
              <span className="routine-html-toolbar-title">Tu rutina</span>
              <button
                type="button"
                className="ai-confirm-close-btn"
                onClick={() => setShowHtmlModal(false)}
                aria-label="Cerrar"
              >
                <X size={18} />
              </button>
            </div>
            <iframe
              className="routine-html-frame"
              srcDoc={routine.html_content}
              title="Rutina de entrenamiento"
              sandbox="allow-scripts"
            />
          </div>
        </div>,
        document.body,
      )}

    </div>
  )
}

export default RoutineModule

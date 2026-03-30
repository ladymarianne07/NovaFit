/**
 * DietModule — Create, view, and manage the user's personalized AI diet plan.
 *
 * Features:
 *   1. AI generation via intake form + free text → nutritionist prompt
 *   2. Viewing: training day vs rest day tabs, meal breakdown, macros, water intake
 *   3. Edit mode: describe changes → AI updates the diet
 *   4. HTML viewer modal with self-contained styled document
 */
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Check,
  ChevronDown,
  Dumbbell,
  Pencil,
  Plus,
  RefreshCw,
  Salad,
  Send,
  Sparkles,
  X,
} from 'lucide-react'
import {
  DietEditRequest,
  DietGenerateRequest,
  DietIntakeData,
  UserDietResponse,
  dietAPI,
} from '../services/api'
import { useAuth } from '../contexts/AuthContext'

// ── Types ────────────────────────────────────────────────────────────────────

interface DietModuleProps {
  className?: string
}

type DayTab = 'training' | 'rest'

const BUDGET_OPTIONS = [
  { value: 'económico', label: 'Económico' },
  { value: 'moderado', label: 'Moderado' },
  { value: 'sin límite', label: 'Sin límite' },
] as const

const COOKING_TIME_OPTIONS = [
  { value: 'mínimo (platos rápidos)', label: 'Mínimo (platos rápidos)' },
  { value: 'moderado (30-45 min)', label: 'Moderado (30-45 min)' },
  { value: 'sin límite', label: 'Sin límite' },
] as const

const DEFAULT_INTAKE: DietIntakeData = {
  meals_count: 5,
  dietary_restrictions: '',
  food_allergies: '',
  health_conditions: '',
  disliked_foods: '',
  budget_level: 'moderado',
  cooking_time: 'moderado (30-45 min)',
  meal_timing_preference: '',
}

// ── RoutineSelect reused pattern — portal-based dropdown ──────────────────────

interface SelectOption { value: string; label: string }
interface DietSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  disabled?: boolean
}

const DietSelect: React.FC<DietSelectProps> = ({ label, value, onChange, options, disabled }) => {
  const [isOpen, setIsOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const [panelStyle, setPanelStyle] = useState<React.CSSProperties>({})
  const selectedLabel = options.find((o) => o.value === value)?.label ?? ''

  useEffect(() => {
    if (!isOpen) return
    const handleClick = (e: MouseEvent) => {
      if (triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [isOpen])

  const handleOpen = () => {
    if (disabled) return
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPanelStyle({
        position: 'fixed',
        top: rect.bottom + 6,
        left: rect.left,
        width: rect.width,
        zIndex: 1300,
      })
    }
    setIsOpen((prev) => !prev)
  }

  return (
    <div className="routine-intake-field">
      <label className="routine-intake-label">{label}</label>
      <button
        ref={triggerRef}
        type="button"
        className="routine-intake-select routine-select-trigger"
        onClick={handleOpen}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{selectedLabel}</span>
        <ChevronDown size={15} style={{ flexShrink: 0, transform: isOpen ? 'rotate(180deg)' : undefined, transition: 'transform 0.2s ease' }} />
      </button>
      {isOpen && createPortal(
        <div className="custom-select-panel" style={panelStyle} role="listbox">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              role="option"
              aria-selected={opt.value === value}
              className={`custom-select-option ${opt.value === value ? 'selected' : ''}`}
              onClick={() => { onChange(opt.value); setIsOpen(false) }}
            >
              <span className="custom-select-option-text">
                <span className="custom-select-option-label">{opt.label}</span>
              </span>
              {opt.value === value && <Check size={15} className="custom-select-check" />}
            </button>
          ))}
        </div>,
        document.body,
      )}
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

const DietModule: React.FC<DietModuleProps> = ({ className }) => {
  const { user } = useAuth()

  // Global state
  const [diet, setDiet] = useState<UserDietResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Creation state
  const [intake, setIntake] = useState<DietIntakeData>(DEFAULT_INTAKE)
  const [freeText, setFreeText] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Missing-data modal
  const [showMissingModal, setShowMissingModal] = useState(false)
  const [missingFields, setMissingFields] = useState<string[]>([])

  // Edit mode
  const [showEditBar, setShowEditBar] = useState(false)
  const [editInstruction, setEditInstruction] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [editError, setEditError] = useState('')

  // HTML viewer modal
  const [showHtmlModal, setShowHtmlModal] = useState(false)

  // Day tab (training vs rest)
  const [dayTab, setDayTab] = useState<DayTab>('training')

  // Expanded meal card
  const [expandedMealId, setExpandedMealId] = useState<string | null>(null)

  // ── Load diet on mount ────────────────────────────────────────────────────

  const loadDiet = useCallback(async () => {
    try {
      const data = await dietAPI.getActive()
      setDiet(data)
    } catch {
      // No active diet yet
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadDiet() }, [loadDiet])

  // ── Helpers ───────────────────────────────────────────────────────────────

  const updateIntake = <K extends keyof DietIntakeData>(field: K, value: DietIntakeData[K]) =>
    setIntake((prev) => ({ ...prev, [field]: value }))

  const openCreateModal = () => {
    setCreateError('')
    setShowCreateModal(true)
  }

  const closeCreateModal = () => {
    setShowCreateModal(false)
    setCreateError('')
    setFreeText('')
    setIntake(DEFAULT_INTAKE)
  }

  const getMissingRequired = (): string[] => {
    const missing: string[] = []
    if (!user?.target_calories && !user?.bmr) {
      missing.push('Perfil nutricional (calorías objetivo)')
    }
    return missing
  }

  // ── Generate ──────────────────────────────────────────────────────────────

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
      const payload: DietGenerateRequest = { intake, free_text: freeText }
      const data = await dietAPI.generate(payload)
      setDiet(data)
      if (data.status === 'ready') {
        closeCreateModal()
      } else if (data.status === 'error') {
        setCreateError(data.error_message || 'Error al generar la dieta.')
      }
    } catch (err: unknown) {
      setCreateError(
        err instanceof Error ? err.message : 'No se pudo generar la dieta. Intentá de nuevo.',
      )
    } finally {
      setIsGenerating(false)
    }
  }

  // ── Edit diet ─────────────────────────────────────────────────────────────

  const handleEdit = async () => {
    if (!editInstruction.trim() || editInstruction.trim().length < 5) return
    setEditError('')
    setIsEditing(true)
    try {
      const payload: DietEditRequest = { edit_instruction: editInstruction.trim() }
      const data = await dietAPI.edit(payload)
      setDiet(data)
      if (data.status === 'ready') {
        setShowEditBar(false)
        setEditInstruction('')
      } else if (data.status === 'error') {
        setEditError(data.error_message || 'Error al editar la dieta.')
      }
    } catch (err: unknown) {
      setEditError(
        err instanceof Error ? err.message : 'No se pudo editar la dieta. Intentá de nuevo.',
      )
    } finally {
      setIsEditing(false)
    }
  }

  const hasActiveDiet = diet?.status === 'ready'
  const dietData = diet?.diet_data
  const activeDay = dayTab === 'training' ? dietData?.training_day : dietData?.rest_day

  // ── Loading ───────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className={`diet-module ${className ?? ''}`}>
        <div className="routine-loading">
          <div className="neon-loader neon-loader--md" aria-hidden="true" />
          <p>Cargando plan de dieta...</p>
        </div>
      </div>
    )
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className={`diet-module ${className ?? ''}`}>
      {/* ══════════════ EMPTY STATE ══════════════ */}
      {!hasActiveDiet ? (
        <div className="routine-empty-state">
          <Salad size={40} className="routine-empty-icon" />
          <p className="routine-empty-title">Todavía no tenés un plan de dieta</p>
          <p className="routine-empty-sub">
            La IA creará tu dieta personalizada basándose en tus calorías objetivo, macros y rutina de entrenamiento.
          </p>
          <button
            type="button"
            className="routine-primary-btn"
            onClick={openCreateModal}
          >
            <Sparkles size={16} />
            Generar mi dieta con IA
          </button>
        </div>
      ) : (
        <>
          {/* ── Header card ── */}
          <div className="routine-ready-card">
            <div className="routine-ready-top">
              <div className="routine-ready-meta">
                <h2 className="routine-ready-title">
                  {dietData?.title ?? 'Mi Dieta'}
                </h2>
                {dietData?.objective_label && (
                  <p className="routine-ready-subtitle">{dietData.objective_label}</p>
                )}
              </div>
              <span className="routine-source-badge ai">✨ Generada con IA</span>
            </div>

            {dietData?.description && (
              <p className="diet-description">{dietData.description}</p>
            )}

            <button
              type="button"
              className="routine-primary-btn"
              onClick={() => setShowHtmlModal(true)}
            >
              Ver plan completo
            </button>

            <div className="routine-ready-actions">
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={openCreateModal}
              >
                <Plus size={14} />
                Regenerar
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

          {/* Calorie summary pills */}
          {dietData && (
            <div className="diet-calorie-summary">
              <div className="diet-cal-pill training">
                <Dumbbell size={14} />
                <span>Entreno: <strong>{Math.round(dietData.target_calories_training)} kcal</strong></span>
              </div>
              <div className="diet-cal-pill rest">
                <span>😴 Descanso: <strong>{Math.round(dietData.target_calories_rest)} kcal</strong></span>
              </div>
            </div>
          )}

          {/* Edit bar */}
          {showEditBar && (
            <div className="routine-edit-bar">
              <p className="routine-edit-label">
                Describí qué querés cambiar en tu dieta:
              </p>
              <div className="routine-edit-row">
                <textarea
                  className="routine-edit-textarea"
                  placeholder="Ej: Cambiá el desayuno por algo más rápido, sacá el salmón, agregá más carbohidratos en el pre-entreno..."
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

          {/* ── Day tabs ── */}
          <div className="diet-day-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={dayTab === 'training'}
              className={`diet-day-tab ${dayTab === 'training' ? 'active' : ''}`}
              onClick={() => { setDayTab('training'); setExpandedMealId(null) }}
            >
              <Dumbbell size={16} />
              <span>Día de Entreno</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={dayTab === 'rest'}
              className={`diet-day-tab ${dayTab === 'rest' ? 'active' : ''}`}
              onClick={() => { setDayTab('rest'); setExpandedMealId(null) }}
            >
              <span>😴</span>
              <span>Día de Descanso</span>
            </button>
          </div>

          {/* ── Day summary ── */}
          {activeDay && (
            <div className="diet-day-section">
              {/* Macros summary row */}
              <div className="diet-macros-row">
                <div className="diet-macro-chip kcal">
                  <span className="diet-macro-value">{Math.round(activeDay.total_calories)}</span>
                  <span className="diet-macro-label">kcal</span>
                </div>
                <div className="diet-macro-chip protein">
                  <span className="diet-macro-value">{Math.round(activeDay.total_protein_g)}g</span>
                  <span className="diet-macro-label">Proteína</span>
                </div>
                <div className="diet-macro-chip carbs">
                  <span className="diet-macro-value">{Math.round(activeDay.total_carbs_g)}g</span>
                  <span className="diet-macro-label">HC</span>
                </div>
                <div className="diet-macro-chip fat">
                  <span className="diet-macro-value">{Math.round(activeDay.total_fat_g)}g</span>
                  <span className="diet-macro-label">Grasas</span>
                </div>
                <div className="diet-macro-chip water">
                  <span className="diet-macro-value">{activeDay.water_ml >= 1000 ? `${(activeDay.water_ml / 1000).toFixed(1)}L` : `${activeDay.water_ml}ml`}</span>
                  <span className="diet-macro-label">💧 Agua</span>
                </div>
              </div>

              {activeDay.notes && (
                <p className="diet-day-notes">{activeDay.notes}</p>
              )}

              {/* Meals list */}
              <div className="diet-meals-list">
                {activeDay.meals.map((meal) => {
                  const isExpanded = expandedMealId === meal.id
                  return (
                    <div key={meal.id} className="diet-meal-card">
                      <button
                        type="button"
                        className="diet-meal-trigger"
                        onClick={() => setExpandedMealId(isExpanded ? null : meal.id)}
                        aria-expanded={isExpanded}
                      >
                        <div className="diet-meal-header">
                          <span className="diet-meal-name">{meal.name}</span>
                          {meal.time && (
                            <span className="diet-meal-time">{meal.time}</span>
                          )}
                          <span className="diet-meal-kcal">{Math.round(meal.total_calories)} kcal</span>
                        </div>
                        <div className="diet-meal-macros">
                          <span>P: {Math.round(meal.total_protein_g)}g</span>
                          <span>HC: {Math.round(meal.total_carbs_g)}g</span>
                          <span>G: {Math.round(meal.total_fat_g)}g</span>
                          <span className="diet-meal-foods-count">{meal.foods.length} alimentos</span>
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="diet-meal-foods">
                          {meal.foods.map((food, idx) => (
                            <div key={idx} className="diet-food-item">
                              <div className="diet-food-row">
                                <span className="diet-food-name">{food.name}</span>
                                <span className="diet-food-kcal">{Math.round(food.calories)} kcal</span>
                              </div>
                              <div className="diet-food-detail">
                                <span>{food.portion}</span>
                                <span>P:{Math.round(food.protein_g)}g · HC:{Math.round(food.carbs_g)}g · G:{Math.round(food.fat_g)}g</span>
                              </div>
                              {food.notes && (
                                <p className="diet-food-notes">{food.notes}</p>
                              )}
                            </div>
                          ))}
                          {meal.notes && (
                            <p className="diet-meal-note">{meal.notes}</p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Health notes */}
              {dietData?.health_notes && dietData.health_notes.length > 0 && (
                <div className="diet-health-notes">
                  <p className="diet-health-notes-title">📋 Recomendaciones</p>
                  <ul>
                    {dietData.health_notes.map((note, i) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                  {dietData.supplement_suggestions && (
                    <p className="diet-supplement">{dietData.supplement_suggestions}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ══════════ CREATE MODAL ══════════ */}
      {showCreateModal && createPortal(
        <div
          className="routine-create-overlay"
          onClick={closeCreateModal}
          role="dialog"
          aria-modal="true"
          aria-label={hasActiveDiet ? 'Regenerar dieta' : 'Generar mi dieta'}
        >
          <div
            className="routine-create-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="routine-create-header">
              <span className="routine-create-header-title">
                {hasActiveDiet ? 'Regenerar dieta' : 'Generar mi dieta con IA'}
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

            <div className="diet-ai-creator">
              {/* Profile macros reminder */}
              {user?.target_calories && (
                <div className="diet-profile-summary">
                  <p className="diet-profile-summary-title">Tu perfil nutricional</p>
                  <div className="diet-profile-pills">
                    <span>{Math.round(user.target_calories)} kcal</span>
                    {user.protein_target_g && <span>P: {Math.round(user.protein_target_g)}g</span>}
                    {user.carbs_target_g && <span>HC: {Math.round(user.carbs_target_g)}g</span>}
                    {user.fat_target_g && <span>G: {Math.round(user.fat_target_g)}g</span>}
                  </div>
                  <p className="diet-profile-note">
                    La IA usará estos objetivos para calcular tus comidas exactas. La rutina de entrenamiento se usa para ajustar las calorías en días de entreno.
                  </p>
                </div>
              )}

              <div className="routine-intake-field">
                <label className="routine-intake-label">
                  Contanos tus preferencias alimentarias{' '}
                  <span className="routine-optional">(opcional pero muy útil)</span>
                </label>
                <textarea
                  className="routine-intake-textarea"
                  placeholder="Ej: Me gusta el pollo, el arroz y la avena. Como a las 7am, 1pm y 7pm. Entreno a las 6pm. No me gusta el pescado azul..."
                  value={freeText}
                  onChange={(e) => setFreeText(e.target.value)}
                  rows={3}
                  disabled={isGenerating}
                />
              </div>

              <div className="routine-intake-form">
                <p className="routine-intake-section-title">
                  Información para personalizar tu dieta
                </p>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Duración por sesión: <strong>{intake.meals_count} comidas por día</strong>
                  </label>
                  <input
                    type="range"
                    min={3}
                    max={8}
                    step={1}
                    value={intake.meals_count}
                    onChange={(e) => updateIntake('meals_count', Number(e.target.value))}
                    className="routine-intake-range"
                    disabled={isGenerating}
                  />
                  <div className="routine-intake-range-labels">
                    <span>3 comidas</span>
                    <span>8 comidas</span>
                  </div>
                </div>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Restricciones dietéticas{' '}
                    <span className="routine-optional">(vegetariano, vegano, sin gluten, etc.)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: Vegetariano, sin lactosa. Si no tenés ninguna dejá vacío."
                    value={intake.dietary_restrictions}
                    onChange={(e) => updateIntake('dietary_restrictions', e.target.value)}
                    rows={2}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Alergias o intolerancias alimentarias{' '}
                    <span className="routine-optional">(opcional)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: Alergia a los frutos secos, intolerancia a la fructosa. Si no tenés ninguna dejá vacío."
                    value={intake.food_allergies}
                    onChange={(e) => updateIntake('food_allergies', e.target.value)}
                    rows={2}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Condiciones de salud relevantes para la nutrición{' '}
                    <span className="routine-optional">(opcional)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: Diabetes tipo 2, hipertensión, hipotiroidismo. Si no tenés ninguna dejá vacío."
                    value={intake.health_conditions}
                    onChange={(e) => updateIntake('health_conditions', e.target.value)}
                    rows={2}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Alimentos que no te gustan o querés evitar{' '}
                    <span className="routine-optional">(opcional)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: No me gusta el hígado, la remolacha ni la coliflor."
                    value={intake.disliked_foods}
                    onChange={(e) => updateIntake('disliked_foods', e.target.value)}
                    rows={2}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-row">
                  <DietSelect
                    label="Presupuesto"
                    value={intake.budget_level}
                    onChange={(v) => updateIntake('budget_level', v)}
                    options={BUDGET_OPTIONS as unknown as SelectOption[]}
                    disabled={isGenerating}
                  />
                  <DietSelect
                    label="Tiempo de cocción"
                    value={intake.cooking_time}
                    onChange={(v) => updateIntake('cooking_time', v)}
                    options={COOKING_TIME_OPTIONS as unknown as SelectOption[]}
                    disabled={isGenerating}
                  />
                </div>

                <div className="routine-intake-field">
                  <label className="routine-intake-label">
                    Horario de comidas preferido{' '}
                    <span className="routine-optional">(opcional)</span>
                  </label>
                  <textarea
                    className="routine-intake-textarea"
                    placeholder="Ej: Desayuno a las 7, almuerzo a las 13, merienda a las 17, cena a las 21."
                    value={intake.meal_timing_preference}
                    onChange={(e) => updateIntake('meal_timing_preference', e.target.value)}
                    rows={2}
                    disabled={isGenerating}
                  />
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
                    Generando dieta personalizada...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Generar mi dieta personalizada
                  </>
                )}
              </button>
            </div>
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

            <p className="routine-missing-title">⚠️ Perfil incompleto</p>
            <p className="routine-missing-sub">
              Para armar la mejor dieta posible necesitamos:
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
              Completá tu perfil nutricional en Configuración o pedile a la IA que use valores estándar.
            </p>
            <div className="routine-missing-actions">
              <button
                type="button"
                className="routine-secondary-btn"
                onClick={() => setShowMissingModal(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="routine-primary-btn"
                onClick={executeGenerate}
              >
                <RefreshCw size={15} />
                Generar con valores estándar
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )}

      {/* ══════════ HTML VIEWER MODAL ══════════ */}
      {showHtmlModal && diet?.html_content && createPortal(
        <div
          className="routine-html-overlay"
          onClick={() => setShowHtmlModal(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Plan de dieta completo"
        >
          <div
            className="routine-html-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="routine-html-toolbar">
              <span className="routine-html-toolbar-title">Tu plan de dieta</span>
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
              srcDoc={diet.html_content}
              title="Plan de dieta personalizado"
              sandbox="allow-scripts"
            />
          </div>
        </div>,
        document.body,
      )}
    </div>
  )
}

export default DietModule

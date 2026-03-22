import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Clock, Dumbbell, Flame, ListChecks, Sparkles, Trash2 } from 'lucide-react'
import RoutineModule from './RoutineModule'
import {
  routineAPI,
  UserRoutineResponse,
  RoutineSession,
  workoutAPI,
  WorkoutDailyEnergyResponse,
  WorkoutSessionCreateRequest,
  WorkoutSessionResponse,
} from '../services/api'

interface WorkoutModuleProps {
  className?: string
}

type IntensityLevel = 'low' | 'medium' | 'high'

interface ParsedWorkoutBlock {
  activity: string
  duration_minutes: number
  intensity: IntensityLevel
}

const MAX_WORKOUT_DURATION_MINUTES = 300

const TEXTUAL_NUMBER_MAP: Record<string, number> = {
  cero: 0,
  un: 1,
  uno: 1,
  una: 1,
  dos: 2,
  tres: 3,
  cuatro: 4,
  cinco: 5,
  seis: 6,
  siete: 7,
  ocho: 8,
  nueve: 9,
  diez: 10,
  once: 11,
  doce: 12,
  quince: 15,
  veinte: 20,
  treinta: 30,
  cuarenta: 40,
  cincuenta: 50,
  sesenta: 60,
  setenta: 70,
  ochenta: 80,
  noventa: 90,
}

const TRAINING_CONTEXT_PATTERNS = [
  /entren/i,
  /entrene/i,
  /entrené/i,
  /ejercit/i,
  /gym/i,
  /gimnasio/i,
  /rutina/i,
  /sesion/i,
  /sesión/i,
  /hice/i,
  /jugue/i,
  /jugué/i,
  /practique/i,
  /practiqué/i,
  /corr/i,
  /camin/i,
  /trot/i,
  /pedal/i,
  /nad/i,
]

const ACTIVITY_ALIASES: Array<{ key: string; aliases: string[]; label: string }> = [
  { key: 'caminar', aliases: ['caminar', 'caminata', 'walking'], label: 'Caminar' },
  { key: 'caminar', aliases: ['marchar', 'senderismo', 'hiking', 'trekking', 'andar'], label: 'Caminar' },
  { key: 'trote', aliases: ['trote', 'trote suave', 'jogging'], label: 'Trote' },
  { key: 'correr', aliases: ['correr', 'running', 'running rapido', 'run'], label: 'Correr' },
  { key: 'ciclismo', aliases: ['ciclismo', 'bicicleta', 'bike', 'cycling'], label: 'Ciclismo' },
  { key: 'spinning', aliases: ['spinning'], label: 'Spinning' },
  { key: 'saltar_cuerda', aliases: ['saltar cuerda', 'cuerda', 'jump rope'], label: 'Saltar cuerda' },
  {
    key: 'fuerza_general',
    aliases: [
      'fuerza',
      'entrenamiento de fuerza',
      'pesas',
      'musculacion',
      'musculación',
      'musculo',
      'músculo',
      'entrene musculacion',
      'entrene musculación',
      'gym',
      'gimnasio',
      'maquinas',
      'máquinas',
      'strength training',
      'weight training',
      'resistencia',
      'calistenia',
      'trx',
      'pesas libres',
      'maquina',
      'máquina',
      'bodybuilding',
      'hipertrofia',
      'full body',
      'torso pierna',
      'torso-pierna',
    ],
    label: 'Fuerza general',
  },
  {
    key: 'pesas_intenso',
    aliases: [
      'pesas intenso',
      'fuerza intensa',
      'musculacion intensa',
      'musculación intensa',
      'gym intenso',
      'gimnasio intenso',
      'al fallo',
      'a tope',
      'pesado',
      'pesada',
    ],
    label: 'Pesas intenso',
  },
  { key: 'crossfit', aliases: ['crossfit', 'cross fit', 'wod'], label: 'CrossFit' },
  {
    key: 'hiit',
    aliases: [
      'hiit',
      'intervalos',
      'interval training',
      'funcional',
      'circuito',
      'tabata',
      'sprints',
      'boxeo',
      'boxing',
      'kickboxing',
      'muay thai',
      'mma',
      'artes marciales',
      'futbol',
      'fútbol',
      'basquet',
      'básquet',
      'basket',
      'baloncesto',
      'handball',
      'hockey',
      'rugby',
      'voley',
      'voleibol',
      'zumba',
      'dance',
      'baile',
    ],
    label: 'HIIT',
  },
  { key: 'yoga', aliases: ['yoga'], label: 'Yoga' },
  { key: 'yoga', aliases: ['movilidad', 'stretching', 'estiramientos', 'elongacion', 'elongación'], label: 'Yoga' },
  { key: 'pilates', aliases: ['pilates', 'reformer'], label: 'Pilates' },
  { key: 'natacion', aliases: ['natacion', 'natación', 'swimming'], label: 'Natación' },
  { key: 'natacion', aliases: ['pileta', 'alberca', 'estilo libre', 'crol'], label: 'Natación' },
  { key: 'remo', aliases: ['remo', 'rowing'], label: 'Remo' },
  { key: 'remo', aliases: ['ergometro', 'ergómetro', 'remoergometro', 'remoergómetro'], label: 'Remo' },
  { key: 'eliptica', aliases: ['eliptica', 'elíptica', 'elliptical'], label: 'Elíptica' },
]

const normalizeText = (value: string) =>
  value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}:.''\s-]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim()

const toSingularTrainingText = (value: string): string => {
  let normalized = normalizeText(value)
  for (const [word, numberValue] of Object.entries(TEXTUAL_NUMBER_MAP)) {
    const regex = new RegExp(`\\b${word}\\b`, 'g')
    normalized = normalized.replace(regex, String(numberValue))
  }

  normalized = normalized
    .replace(/\b(media hora)\b/g, '30 min')
    .replace(/\b(cuarto de hora)\b/g, '15 min')
    .replace(/\b(hora y media)\b/g, '1 h 30 min')
    .replace(/\b(\d+)\s+hora\s+y\s+media\b/g, (_, hours: string) => `${hours} h 30 min`)
    .replace(/\b(\d+)\s*h\s*(\d{1,2})\b/g, '$1 h $2 min')

  return normalized
}

const hasTrainingContext = (segment: string) => {
  const normalized = toSingularTrainingText(segment)
  return TRAINING_CONTEXT_PATTERNS.some((pattern) => pattern.test(normalized))
}

const getLocalDateISO = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const parseIntensity = (segment: string): IntensityLevel => {
  const normalized = toSingularTrainingText(segment)

  if (/(alta|intensa|fuerte|high|hard|vigorous|pesad[oa]|a tope|al fallo|explosiv[oa])/i.test(normalized)) {
    return 'high'
  }

  if (/(baja|suave|ligera|light|low|tranqui|tranquila|recuperacion|recuperacion activa)/i.test(normalized)) {
    return 'low'
  }

  return 'medium'
}

const parseDurationMinutes = (segment: string): number | null => {
  const normalized = toSingularTrainingText(segment).replace(',', '.')

  const hourMinuteMatch = normalized.match(/\b(\d+(?:\.\d+)?)\s*h(?:ora|oras)?\s*(\d{1,2})\s*(?:m|min|minuto|minutos)?\b/)
  if (hourMinuteMatch) {
    const hours = Number(hourMinuteMatch[1])
    const minutes = Number(hourMinuteMatch[2])

    if (Number.isNaN(hours) || Number.isNaN(minutes) || hours < 0 || minutes < 0 || minutes >= 60) {
      return null
    }

    const total = Math.round(hours * 60 + minutes)
    if (total <= 0 || total > MAX_WORKOUT_DURATION_MINUTES) {
      return null
    }

    return total
  }

  const hhmmMatch = normalized.match(/\b(\d{1,2}):(\d{2})\b/)
  if (hhmmMatch) {
    const hours = Number(hhmmMatch[1])
    const minutes = Number(hhmmMatch[2])
    const total = Math.round(hours * 60 + minutes)

    if (Number.isNaN(total) || total <= 0 || total > MAX_WORKOUT_DURATION_MINUTES) {
      return null
    }

    return total
  }

  const unitMatch = normalized.match(/(\d+(?:\.\d+)?)\s*(h|hora|horas|min|minuto|minutos|m)\b/)
  if (unitMatch) {
    const value = Number(unitMatch[1])
    const unit = unitMatch[2]

    if (Number.isNaN(value) || value <= 0) {
      return null
    }

    if (unit.startsWith('h')) {
      const minutes = Math.round(value * 60)
      return minutes > 0 && minutes <= MAX_WORKOUT_DURATION_MINUTES ? minutes : null
    }

    const minutes = Math.round(value)
    return minutes > 0 && minutes <= MAX_WORKOUT_DURATION_MINUTES ? minutes : null
  }

  const apostropheMatch = normalized.match(/(\d+)\s*['']/)
  if (apostropheMatch) {
    const value = Number(apostropheMatch[1])
    return Number.isNaN(value) || value <= 0 || value > MAX_WORKOUT_DURATION_MINUTES
      ? null
      : Math.round(value)
  }

  const plainNumberMatch = normalized.match(/\b(\d{1,3})\b/)
  if (plainNumberMatch && hasTrainingContext(normalized)) {
    const value = Number(plainNumberMatch[1])
    return Number.isNaN(value) || value <= 0 || value > MAX_WORKOUT_DURATION_MINUTES ? null : value
  }

  return null
}

const scoreAliasMatch = (normalizedSegment: string, normalizedAlias: string): number => {
  if (!normalizedAlias) return 0
  if (normalizedSegment === normalizedAlias) return normalizedAlias.length + 100

  const escapedAlias = normalizedAlias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const aliasBoundaryRegex = new RegExp(`(^|\\s)${escapedAlias}(\\s|$)`, 'i')
  if (aliasBoundaryRegex.test(normalizedSegment)) {
    return normalizedAlias.length + 50
  }

  return normalizedSegment.includes(normalizedAlias) ? normalizedAlias.length : 0
}

const resolveHeuristicActivityKey = (segment: string): { key: string; label: string } | null => {
  const normalized = toSingularTrainingText(segment)

  const heuristicRules: Array<{ pattern: RegExp; key: string; label: string }> = [
    { pattern: /futbol|futbol|basket|basquet|baloncesto|rugby|hockey|handball|voley|voleibol|partido/, key: 'hiit', label: 'HIIT' },
    { pattern: /boxeo|boxing|kickboxing|muay thai|mma|sparring|combate/, key: 'hiit', label: 'HIIT' },
    { pattern: /calistenia|trx|peso libre|maquina|maquinas|muscul|pesas|fuerza/, key: 'fuerza_general', label: 'Fuerza general' },
    { pattern: /movilidad|estir|elong|stretching|recuperacion activa/, key: 'yoga', label: 'Yoga' },
    { pattern: /senderismo|hiking|trekking|caminat|marchar/, key: 'caminar', label: 'Caminar' },
    { pattern: /nado|nataci|pileta|alberca|crol/, key: 'natacion', label: 'Natación' },
    { pattern: /remo|ergometro|ergometro/, key: 'remo', label: 'Remo' },
    { pattern: /eliptic|eliptica|eliptica/, key: 'eliptica', label: 'Elíptica' },
    { pattern: /zumba|baile|dance|aerobico|aerobica/, key: 'hiit', label: 'HIIT' },
  ]

  for (const rule of heuristicRules) {
    if (rule.pattern.test(normalized)) {
      return { key: rule.key, label: rule.label }
    }
  }

  if (hasTrainingContext(normalized)) {
    return { key: 'fuerza_general', label: 'Fuerza general' }
  }

  return null
}

const resolveActivityKey = (segment: string): { key: string; label: string } | null => {
  const normalized = toSingularTrainingText(segment)

  let bestMatch: { key: string; label: string; score: number } | null = null

  for (const candidate of ACTIVITY_ALIASES) {
    for (const alias of candidate.aliases) {
      const normalizedAlias = toSingularTrainingText(alias)
      const score = scoreAliasMatch(normalized, normalizedAlias)
      if (score > 0) {
        if (!bestMatch || score > bestMatch.score) {
          bestMatch = { key: candidate.key, label: candidate.label, score }
        }
      }
    }
  }

  if (!bestMatch) {
    return resolveHeuristicActivityKey(segment)
  }

  return { key: bestMatch.key, label: bestMatch.label }
}

const parseWorkoutInput = (input: string): ParsedWorkoutBlock[] => {
  const normalizedInput = input.trim()
  if (!normalizedInput) {
    throw new Error('Escribe tu entrenamiento para poder procesarlo.')
  }

  const rawSegments = normalizedInput
    .split(/[+,;]+|\s+y\s+|\s+luego\s+|\s+despues\s+|\s+después\s+|\n+/i)
    .map((part) => part.trim())
    .filter(Boolean)

  const segments = rawSegments.length > 0 ? rawSegments : [normalizedInput]

  const blocks = segments.map((segment) => {
    const activity = resolveActivityKey(segment)
    if (!activity) {
      throw new Error(`No reconocí la actividad en: "${segment}". Puedes agregar deporte o tipo de entreno (ej: gym, fútbol, boxeo, movilidad).`)
    }

    const durationMinutes = parseDurationMinutes(segment)
    if (!durationMinutes) {
      throw new Error(`Falta duración para "${activity.label}". Ejemplo: 45 min.`)
    }

    return {
      activity: activity.key,
      duration_minutes: durationMinutes,
      intensity: parseIntensity(segment),
    }
  })

  if (blocks.length === 0) {
    throw new Error('No pude extraer bloques de entrenamiento del texto.')
  }

  return blocks
}

const formatIntensityLabel = (intensity?: string | null) => {
  if (intensity === 'high') return 'Alta'
  if (intensity === 'low') return 'Baja'
  return 'Media'
}

const DAY_NAMES_ES = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

const findTodaySession = (routine: UserRoutineResponse | null): RoutineSession | null => {
  if (!routine?.routine_data?.sessions?.length) return null
  const today = DAY_NAMES_ES[new Date().getDay()]
  return (
    routine.routine_data.sessions.find((s) =>
      s.day_label?.toLowerCase().includes(today.toLowerCase()),
    ) ?? routine.routine_data.sessions[0]
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

const WorkoutModule: React.FC<WorkoutModuleProps> = ({ className = '' }) => {
  const targetDate = useMemo(() => getLocalDateISO(), [])

  // ── Data state ───────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState<WorkoutSessionResponse[]>([])
  const [dailyEnergy, setDailyEnergy] = useState<WorkoutDailyEnergyResponse | null>(null)
  const [routine, setRoutine] = useState<UserRoutineResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [listError, setListError] = useState('')

  // ── Tab state ────────────────────────────────────────────────────────────
  const [moduleTab, setModuleTab] = useState<'sessions' | 'routine'>('sessions')

  // ── Routine toggle ───────────────────────────────────────────────────────
  const [routineCompleted, setRoutineCompleted] = useState(false)

  // ── AI flow state ────────────────────────────────────────────────────────
  const [showAiForm, setShowAiForm] = useState(false)
  const [showRoutineModal, setShowRoutineModal] = useState(false)
  const [aiInput, setAiInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  // ── Delete state ─────────────────────────────────────────────────────────
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(null)

  // ── Derived values ───────────────────────────────────────────────────────
  const hasActiveRoutine = routine?.status === 'ready'
  const todaySession = useMemo(() => findTodaySession(routine), [routine])
  const routineKcal = Math.round(todaySession?.estimated_calories_per_session ?? 0)
  const sessionDuration = (routine?.intake_data as Record<string, unknown>)?.session_duration_minutes as number ?? 60

  const exerciseKcal = (dailyEnergy?.exercise_kcal_est ?? 0) + (routineCompleted ? routineKcal : 0)
  const intakeKcal = dailyEnergy?.intake_kcal ?? 0
  const netKcal = Math.round(intakeKcal - exerciseKcal)
  const showCalories = intakeKcal > 0 || exerciseKcal > 0

  // ── Data fetching ────────────────────────────────────────────────────────
  const fetchWorkoutData = useCallback(async () => {
    setIsLoading(true)
    setListError('')
    try {
      const [sessionsData, energyData, routineData] = await Promise.all([
        workoutAPI.listSessions(targetDate),
        workoutAPI.getDailyEnergy(targetDate),
        routineAPI.getActive().catch(() => null),
      ])
      setSessions(sessionsData)
      setDailyEnergy(energyData)
      setRoutine(routineData)
    } catch {
      setListError('No se pudo cargar el resumen de entrenamiento.')
    } finally {
      setIsLoading(false)
    }
  }, [targetDate])

  useEffect(() => { fetchWorkoutData() }, [fetchWorkoutData])

  useEffect(() => {
    const handler = () => fetchWorkoutData()
    window.addEventListener('nutrition:updated', handler)
    window.addEventListener('workout:updated', handler)
    return () => {
      window.removeEventListener('nutrition:updated', handler)
      window.removeEventListener('workout:updated', handler)
    }
  }, [fetchWorkoutData])

  // ── AI form ──────────────────────────────────────────────────────────────
  const parsedPreview = useMemo(() => {
    if (!aiInput.trim()) return []
    try { return parseWorkoutInput(aiInput) } catch { return [] }
  }, [aiInput])

  const handleAiBtnClick = () => {
    if (hasActiveRoutine && !routineCompleted) {
      setShowRoutineModal(true)
    } else {
      setShowAiForm(true)
    }
  }

  const handleRoutineModalOption = (replaces: boolean) => {
    setShowRoutineModal(false)
    if (replaces) setRoutineCompleted(true)
    setShowAiForm(true)
  }

  const handleCreateSession = async () => {
    try {
      setIsSubmitting(true)
      setSubmitError('')

      const blocks = parseWorkoutInput(aiInput)
      const payload: WorkoutSessionCreateRequest = {
        session_date: targetDate,
        source: 'ai',
        status: 'final',
        raw_input: aiInput.trim(),
        blocks,
      }
      await workoutAPI.createSession(payload)
      await fetchWorkoutData()
      window.dispatchEvent(new Event('workout:updated'))
      setAiInput('')
      setShowAiForm(false)
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string' && detail.trim()) setSubmitError(detail)
      else if (err instanceof Error) setSubmitError(err.message)
      else setSubmitError('No se pudo guardar el entrenamiento. Intenta nuevamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteSession = async (sessionId: number) => {
    try {
      setDeletingSessionId(sessionId)
      await workoutAPI.deleteSession(sessionId)
      await fetchWorkoutData()
      window.dispatchEvent(new Event('workout:updated'))
    } catch {
      setListError('No se pudo eliminar el entrenamiento.')
    } finally {
      setDeletingSessionId(null)
    }
  }

  const closeAiForm = () => {
    setShowAiForm(false)
    setAiInput('')
    setSubmitError('')
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <section className={`workout-module ${className}`.trim()} aria-label="Módulo de entrenamiento">

      {/* ── Module tabs ── */}
      <div className="module-tabs" role="tablist" aria-label="Secciones de entrenamiento">
        <button
          type="button"
          role="tab"
          aria-selected={moduleTab === 'sessions'}
          className={`module-tab ${moduleTab === 'sessions' ? 'active' : ''}`}
          onClick={() => setModuleTab('sessions')}
        >
          <Dumbbell size={20} />
          <span>Mis Entrenos</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={moduleTab === 'routine'}
          className={`module-tab ${moduleTab === 'routine' ? 'active' : ''}`}
          onClick={() => setModuleTab('routine')}
        >
          <ListChecks size={20} />
          <span>Mi Rutina</span>
        </button>
      </div>

      {moduleTab === 'routine' ? (
        <RoutineModule />
      ) : (
        <>
          {/* ── Ingresar entreno por IA ── */}
          <button type="button" className="workout-ai-btn" onClick={handleAiBtnClick}>
            <Sparkles size={15} />
            Ingresar entreno por IA
          </button>

          {/* ── AI input form (inline) ── */}
          {showAiForm && (
            <div className="workout-ai-form">
              <label className="workout-ai-label" htmlFor="ai-workout-input">
                Describe tu entrenamiento
              </label>
              <p className="workout-ai-hint">
                Ejemplo: <strong>45 min gym + 20 min trote medio</strong>
              </p>
              <textarea
                id="ai-workout-input"
                className="workout-ai-textarea"
                placeholder="Ej: 30 min trote suave + 25 min pesas intenso"
                rows={3}
                value={aiInput}
                onChange={(e) => { setSubmitError(''); setAiInput(e.target.value) }}
              />
              {parsedPreview.length > 0 && (
                <div className="workout-preview">
                  {parsedPreview.map((block, index) => (
                    <span key={`${block.activity}-${index}`} className="workout-preview-chip">
                      {block.activity} · {block.duration_minutes} min · {formatIntensityLabel(block.intensity)}
                    </span>
                  ))}
                </div>
              )}
              {submitError && <p className="workout-form-error" role="alert">{submitError}</p>}
              <div className="workout-ai-form-actions">
                <button type="button" className="workout-ai-form-cancel" onClick={closeAiForm}>
                  Cancelar
                </button>
                <button
                  type="button"
                  className="workout-ai-form-submit"
                  onClick={handleCreateSession}
                  disabled={isSubmitting || !aiInput.trim()}
                >
                  <Sparkles size={14} />
                  {isSubmitting ? 'Calculando...' : 'Guardar'}
                </button>
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="workout-loading">
              <div className="neon-loader neon-loader--sm" aria-hidden="true" />
              <p>Cargando...</p>
            </div>
          ) : (
            <>
              {/* ── Próximo entreno / Empty state ── */}
              {hasActiveRoutine && todaySession ? (
                <div className={`workout-proximo-card${routineCompleted ? ' completed' : ''}`}>
                  <div className="workout-proximo-top">
                    <div className="workout-proximo-info">
                      <p className="workout-proximo-section-label">Mi Rutina</p>
                      <p className="workout-proximo-title">{todaySession.title}</p>
                      <p className="workout-proximo-sub">
                        {todaySession.exercises?.length ?? 0} ejercicios
                      </p>
                    </div>
                    <span className={`workout-day-tag${routineCompleted ? ' done' : ''}`}>
                      {routineCompleted ? '✓ ' : ''}
                      {todaySession.day_label?.split('·')[0]?.trim() ?? 'HOY'}
                    </span>
                  </div>

                  <div className="workout-proximo-pills">
                    <span className="workout-proximo-pill">
                      <Clock size={9} />
                      {sessionDuration} min
                    </span>
                    <span className="workout-proximo-pill">
                      <Flame size={9} />
                      {routineKcal} kcal
                    </span>
                    <span className="workout-proximo-pill">Media</span>
                  </div>

                  <div className={`workout-toggle-row${routineCompleted ? ' done' : ''}`}>
                    <div>
                      <p className="workout-toggle-label">
                        {routineCompleted ? 'Completado' : 'Marcar como completado'}
                      </p>
                      <p className="workout-toggle-sub">
                        {routineCompleted
                          ? `-${routineKcal} kcal aplicadas`
                          : `Resta ${routineKcal} kcal del día`}
                      </p>
                    </div>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={routineCompleted}
                      className={`workout-toggle-track${routineCompleted ? ' on' : ''}`}
                      onClick={() => setRoutineCompleted((c) => !c)}
                      aria-label="Marcar rutina como completada"
                    >
                      <span className="workout-toggle-thumb" />
                    </button>
                  </div>
                </div>
              ) : !hasActiveRoutine ? (
                <div className="workout-empty-card">
                  <Dumbbell size={22} className="workout-empty-icon" />
                  <p className="workout-empty-title">Sin entreno programado</p>
                  <p className="workout-empty-sub">
                    No tenés una rutina activa. Ingresá un entreno por IA o subí tu rutina en la pestaña "Mi Rutina".
                  </p>
                </div>
              ) : null}

              {/* ── Entrenamientos de hoy ── */}
              <div className="workout-historial-section">
                <p className="workout-section-label">Entrenamientos de hoy</p>
                <div className="workout-historial-card">
                  {listError && <p className="workout-form-error">{listError}</p>}

                  {sessions.length === 0 && !routineCompleted ? (
                    <p className="workout-historial-empty">Sin entrenamientos registrados hoy</p>
                  ) : (
                    <>
                      {/* Routine completed synthetic item */}
                      {routineCompleted && todaySession && (
                        <div className="workout-historial-item">
                          <div className="workout-historial-info">
                            <p className="workout-historial-name">
                              {todaySession.title}
                              <span className="workout-tag-rutina">Rutina</span>
                            </p>
                            <p className="workout-historial-meta">
                              {sessionDuration} min · completado
                            </p>
                          </div>
                          <span className="workout-historial-kcal">-{routineKcal} kcal</span>
                        </div>
                      )}

                      {/* AI sessions */}
                      {sessions.map((session) => (
                        <div key={session.id} className="workout-historial-item">
                          <div className="workout-historial-info">
                            <p className="workout-historial-name">
                              Entreno #{session.id}
                              <span className="workout-tag-ia">IA</span>
                            </p>
                            <p className="workout-historial-meta">
                              {session.blocks.reduce((sum, b) => sum + b.duration_minutes, 0)} min
                            </p>
                          </div>
                          <div className="workout-historial-right">
                            <span className="workout-historial-kcal">
                              -{Math.round(session.total_kcal_est ?? 0)} kcal
                            </span>
                            <button
                              type="button"
                              className="workout-historial-delete"
                              onClick={() => handleDeleteSession(session.id)}
                              disabled={deletingSessionId === session.id}
                              aria-label="Eliminar entrenamiento"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </div>

              {/* ── Calorías del día ── */}
              {showCalories && (
                <div className="workout-cal-section">
                  <p className="workout-section-label">Calorías del día</p>
                  <div className="workout-cal-card">
                    <div className="workout-cal-row">
                      <span className="workout-cal-name">Ingeridas</span>
                      <span className="workout-cal-val">{Math.round(intakeKcal)} kcal</span>
                    </div>
                    <div className="workout-cal-row">
                      <span className="workout-cal-name">Ejercicio</span>
                      <span className="workout-cal-val neg">
                        {exerciseKcal > 0 ? '-' : ''}{Math.round(exerciseKcal)} kcal
                      </span>
                    </div>
                    <div className="workout-cal-row last">
                      <span className="workout-cal-name">Neto</span>
                      <span className={`workout-cal-val net${netKcal < 0 ? ' surplus' : ''}`}>
                        {netKcal} kcal
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ── Routine day modal (bottom sheet) ── */}
          {showRoutineModal && (
            <div
              className="workout-ia-overlay"
              onClick={() => setShowRoutineModal(false)}
              role="dialog"
              aria-modal="true"
              aria-label="Confirmar tipo de entreno"
            >
              <div className="workout-ia-sheet" onClick={(e) => e.stopPropagation()}>
                <div className="workout-ia-handle" />
                <p className="workout-ia-title">¿Este es tu entreno del día?</p>
                <p className="workout-ia-sub">
                  Tenés "{todaySession?.title ?? 'tu sesión'}" programado para hoy. Si este entreno
                  reemplaza al de la rutina, no se contarán dos veces las calorías.
                </p>
                <button
                  type="button"
                  className="workout-ia-option"
                  onClick={() => handleRoutineModalOption(true)}
                >
                  <p className="workout-ia-option-title">✓ Sí, reemplaza mi entreno de hoy</p>
                  <p className="workout-ia-option-sub">
                    Se marca "{todaySession?.title}" como completado automáticamente
                  </p>
                </button>
                <button
                  type="button"
                  className="workout-ia-option"
                  onClick={() => handleRoutineModalOption(false)}
                >
                  <p className="workout-ia-option-title">+ No, es un entreno extra</p>
                  <p className="workout-ia-option-sub">
                    Se registra aparte y las calorías se suman por separado
                  </p>
                </button>
                <button
                  type="button"
                  className="workout-ia-cancel-btn"
                  onClick={() => setShowRoutineModal(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default WorkoutModule

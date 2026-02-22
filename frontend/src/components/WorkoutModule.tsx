import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Brain, ChevronLeft, ChevronRight, Dumbbell, Flame, Sparkles, Trash2 } from 'lucide-react'
import {
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
    .replace(/[^\p{L}\p{N}:.'’\s-]/gu, ' ')
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

  const apostropheMatch = normalized.match(/(\d+)\s*['’]/)
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

const WorkoutModule: React.FC<WorkoutModuleProps> = ({ className = '' }) => {
  const targetDate = useMemo(() => getLocalDateISO(), [])

  const [sessions, setSessions] = useState<WorkoutSessionResponse[]>([])
  const [dailyEnergy, setDailyEnergy] = useState<WorkoutDailyEnergyResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [listError, setListError] = useState('')

  const [isAiOpen, setIsAiOpen] = useState(false)
  const [aiInput, setAiInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const [activeSessionIndex, setActiveSessionIndex] = useState(0)
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(null)

  const sessionTouchStartXRef = useRef<number | null>(null)

  const fetchWorkoutData = useCallback(async () => {
    setIsLoading(true)
    setListError('')

    try {
      const [sessionsData, energyData] = await Promise.all([
        workoutAPI.listSessions(targetDate),
        workoutAPI.getDailyEnergy(targetDate),
      ])

      setSessions(sessionsData)
      setDailyEnergy(energyData)
    } catch {
      setListError('No se pudo cargar el resumen de entrenamiento.')
    } finally {
      setIsLoading(false)
    }
  }, [targetDate])

  useEffect(() => {
    fetchWorkoutData()
  }, [fetchWorkoutData])

  useEffect(() => {
    const handler = () => {
      fetchWorkoutData()
    }

    window.addEventListener('nutrition:updated', handler)
    window.addEventListener('workout:updated', handler)

    return () => {
      window.removeEventListener('nutrition:updated', handler)
      window.removeEventListener('workout:updated', handler)
    }
  }, [fetchWorkoutData])

  useEffect(() => {
    setActiveSessionIndex((current) => {
      if (sessions.length === 0) return 0
      return Math.min(current, sessions.length - 1)
    })
  }, [sessions.length])

  const parsedPreview = useMemo(() => {
    if (!aiInput.trim()) {
      return []
    }

    try {
      return parseWorkoutInput(aiInput)
    } catch {
      return []
    }
  }, [aiInput])

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
      setIsAiOpen(false)
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      if (typeof detail === 'string' && detail.trim()) {
        setSubmitError(detail)
      } else if (error instanceof Error) {
        setSubmitError(error.message)
      } else {
        setSubmitError('No se pudo guardar el entrenamiento. Intenta nuevamente.')
      }
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

  const handleSessionsTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    sessionTouchStartXRef.current = event.touches[0]?.clientX ?? null
  }

  const handleSessionsTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    if (sessionTouchStartXRef.current === null) return

    const endX = event.changedTouches[0]?.clientX ?? sessionTouchStartXRef.current
    const deltaX = endX - sessionTouchStartXRef.current
    const swipeThreshold = 45

    if (Math.abs(deltaX) < swipeThreshold) {
      sessionTouchStartXRef.current = null
      return
    }

    if (deltaX < 0) {
      setActiveSessionIndex((current) => Math.min(current + 1, sessions.length - 1))
    } else {
      setActiveSessionIndex((current) => Math.max(current - 1, 0))
    }

    sessionTouchStartXRef.current = null
  }

  return (
    <section className={`workout-module ${className}`.trim()} aria-label="Módulo de entrenamiento">
      <div className="workout-top-action">
        <button
          type="button"
          className="nutrition-primary-button"
          onClick={() => setIsAiOpen((current) => !current)}
        >
          <Brain size={16} /> {isAiOpen ? 'Cerrar ingreso IA' : 'Ingresar entreno por IA'}
        </button>
      </div>

      {isAiOpen && (
        <article className="nutrition-card workout-panel" role="region" aria-label="Ingreso de entrenamiento por IA">
          <label className="nutrition-ai-label" htmlFor="ai-workout-input">
            Describe tu entrenamiento
          </label>

          <p className="nutrition-ai-hint">
            Ejemplo: <strong>45 min caminar intensidad media + 20 min hiit alta</strong>
          </p>

          <textarea
            id="ai-workout-input"
            className="nutrition-ai-textarea"
            placeholder="Ej: 30 min trote suave + 25 min pesas intenso"
            rows={4}
            value={aiInput}
            onChange={(event) => {
              setSubmitError('')
              setAiInput(event.target.value)
            }}
          />

          {parsedPreview.length > 0 && (
            <div className="workout-preview" aria-label="Vista previa del entrenamiento detectado">
              {parsedPreview.map((block, index) => (
                <span key={`${block.activity}-${index}`} className="workout-preview-chip">
                  {index + 1}. {block.activity} · {block.duration_minutes} min · {formatIntensityLabel(block.intensity)}
                </span>
              ))}
            </div>
          )}

          {submitError && (
            <p className="error-message" role="alert">
              {submitError}
            </p>
          )}

          <div className="nutrition-ai-footer">
            <button
              type="button"
              className="nutrition-primary-button"
              onClick={handleCreateSession}
              disabled={isSubmitting}
            >
              <Sparkles size={16} /> {isSubmitting ? 'Calculando...' : 'Guardar entrenamiento'}
            </button>
          </div>
        </article>
      )}

      <article className="nutrition-card workout-panel" role="region" aria-label="Impacto calórico del entrenamiento">
        <div className="nutrition-card-header">
          <h3 className="nutrition-card-title">
            <Flame size={18} /> Calorías del día (entreno)
          </h3>
        </div>

        {dailyEnergy ? (
          <div className="workout-energy-grid">
            <div className="workout-energy-pill intake">
              <span>Ingeridas</span>
              <strong>{Math.round(dailyEnergy.intake_kcal)} kcal</strong>
            </div>
            <div className="workout-energy-pill burned">
              <span>Ejercicio</span>
              <strong>-{Math.round(dailyEnergy.exercise_kcal_est)} kcal</strong>
            </div>
            <div className="workout-energy-pill net">
              <span>Neto</span>
              <strong>{Math.round(dailyEnergy.net_kcal_est)} kcal</strong>
            </div>
          </div>
        ) : (
          <div className="nutrition-empty-state">
            <p>No hay datos de energía para hoy todavía.</p>
          </div>
        )}
      </article>

      <article className="nutrition-card workout-panel" role="region" aria-label="Mis entrenamientos">
        <div className="nutrition-card-header">
          <h3 className="nutrition-card-title">
            <Dumbbell size={18} /> Mis entrenamientos
          </h3>
        </div>

        {listError && (
          <p className="error-message" role="alert">
            {listError}
          </p>
        )}

        {isLoading ? (
          <div className="nutrition-empty-state">
            <div className="loading-stack">
              <div className="neon-loader neon-loader--sm" aria-hidden="true"></div>
              <p>Cargando entrenamientos...</p>
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="nutrition-empty-state">
            <p>Hoy todavía no cargaste entrenamientos.</p>
          </div>
        ) : (
          <div className="nutrition-meals-slider">
            <div className="nutrition-slider-controls">
              <button
                type="button"
                className="nutrition-slider-nav"
                onClick={() => setActiveSessionIndex((current) => Math.max(current - 1, 0))}
                disabled={activeSessionIndex === 0}
                aria-label="Ver entrenamiento anterior"
              >
                <ChevronLeft size={16} />
              </button>

              <p className="nutrition-slider-indicator">
                Entreno {activeSessionIndex + 1} de {sessions.length}
              </p>

              <button
                type="button"
                className="nutrition-slider-nav"
                onClick={() => setActiveSessionIndex((current) => Math.min(current + 1, sessions.length - 1))}
                disabled={activeSessionIndex === sessions.length - 1}
                aria-label="Ver entrenamiento siguiente"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div
              className="nutrition-slider-window"
              onTouchStart={handleSessionsTouchStart}
              onTouchEnd={handleSessionsTouchEnd}
            >
              <div
                className="nutrition-slider-track"
                style={{ transform: `translate3d(-${activeSessionIndex * 100}%, 0, 0)` }}
              >
                {sessions.map((session) => (
                  <article key={session.id} className="nutrition-meal-item workout-session-item">
                    <div className="nutrition-meal-top">
                      <div className="nutrition-meal-title-group">
                        <p className="nutrition-meal-name">Entreno #{session.id}</p>
                        <span className="nutrition-meal-type-badge workout">
                          {session.source === 'ai' ? 'IA' : session.source}
                        </span>
                      </div>

                      <div className="nutrition-meal-actions">
                        <span className="nutrition-meal-time">
                          {Math.round(session.total_kcal_est ?? 0)} kcal
                        </span>
                        <button
                          type="button"
                          className="nutrition-meal-delete"
                          onClick={() => handleDeleteSession(session.id)}
                          disabled={deletingSessionId === session.id}
                          aria-label="Eliminar entrenamiento"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    <div className="workout-session-blocks">
                      {session.blocks.map((block) => (
                        <div key={block.id} className="workout-session-block-row">
                          <span>Bloque {block.block_order}</span>
                          <span>{block.duration_minutes} min</span>
                          <span>{formatIntensityLabel(block.intensity_level)}</span>
                          <strong>{Math.round(block.kcal_est ?? 0)} kcal</strong>
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="nutrition-slider-dots" role="tablist" aria-label="Selector de entrenamientos">
              {sessions.map((session, index) => (
                <button
                  key={session.id}
                  type="button"
                  className={`nutrition-slider-dot ${index === activeSessionIndex ? 'active' : ''}`}
                  onClick={() => setActiveSessionIndex(index)}
                  aria-label={`Ir al entrenamiento ${index + 1}`}
                  aria-current={index === activeSessionIndex}
                />
              ))}
            </div>
          </div>
        )}
      </article>
    </section>
  )
}

export default WorkoutModule

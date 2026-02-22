import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  Calculator,
  CalendarClock,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Flame,
  Ruler,
  Save,
  Scale,
  Target,
  UserRound,
} from 'lucide-react'
import { FitnessObjective, User, usersAPI, SkinfoldCalculationResult, SkinfoldValues } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import CustomSelect from './UI/CustomSelect'

interface ProfileBiometricsPanelProps {
  user: User
}

type SiteKey = keyof SkinfoldValues
type ProfileSection = 'personal' | 'skinfolds'

const SITES: Array<{ key: SiteKey; label: string; helper: string }> = [
  { key: 'chest_mm', label: 'Pecho (pectoral)', helper: 'Pliegue diagonal entre axila y pezón.' },
  { key: 'midaxillary_mm', label: 'Axilar media', helper: 'Línea media axilar al nivel del xifoides.' },
  { key: 'triceps_mm', label: 'Tríceps', helper: 'Parte posterior del brazo, punto medio húmero.' },
  { key: 'subscapular_mm', label: 'Subescapular', helper: 'Debajo del ángulo inferior de la escápula.' },
  { key: 'abdomen_mm', label: 'Abdomen', helper: 'A 2 cm del ombligo, pliegue vertical.' },
  { key: 'suprailiac_mm', label: 'Suprailíaco', helper: 'Encima de la cresta ilíaca, diagonal.' },
  { key: 'thigh_mm', label: 'Muslo', helper: 'Cara anterior, mitad entre cadera y rodilla.' },
]

const OBJECTIVE_OPTIONS: Array<{ value: FitnessObjective; label: string }> = [
  { value: 'maintenance', label: 'Mantenimiento' },
  { value: 'fat_loss', label: 'Pérdida de grasa' },
  { value: 'muscle_gain', label: 'Ganancia muscular' },
  { value: 'body_recomp', label: 'Recomposición corporal' },
  { value: 'performance', label: 'Rendimiento' },
]

const INTENSITY_OPTIONS = [
  { value: 1, label: '1 · Conservador' },
  { value: 2, label: '2 · Moderado' },
  { value: 3, label: '3 · Agresivo' },
]

const parseOptionalNumber = (value: string): number | undefined => {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? undefined : parsed
}

const ProfileBiometricsPanel: React.FC<ProfileBiometricsPanelProps> = ({ user }) => {
  const { updateBiometrics, updateObjective } = useAuth()
  const { showError, showSuccess } = useToast()

  const [activeSection, setActiveSection] = useState<ProfileSection>('personal')
  const [useTriplicate, setUseTriplicate] = useState(false)
  const [activeSiteIndex, setActiveSiteIndex] = useState(0)
  const skinfoldTouchStartX = useRef<number | null>(null)

  const [values, setValues] = useState<Record<SiteKey, string>>({
    chest_mm: '',
    midaxillary_mm: '',
    triceps_mm: '',
    subscapular_mm: '',
    abdomen_mm: '',
    suprailiac_mm: '',
    thigh_mm: '',
  })

  const [triplicate, setTriplicate] = useState<Record<SiteKey, [string, string, string]>>({
    chest_mm: ['', '', ''],
    midaxillary_mm: ['', '', ''],
    triceps_mm: ['', '', ''],
    subscapular_mm: ['', '', ''],
    abdomen_mm: ['', '', ''],
    suprailiac_mm: ['', '', ''],
    thigh_mm: ['', '', ''],
  })

  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isCalculating, setIsCalculating] = useState(false)
  const [result, setResult] = useState<SkinfoldCalculationResult | null>(null)
  const [history, setHistory] = useState<SkinfoldCalculationResult[]>([])

  const [ageInput, setAgeInput] = useState(user.age ? String(user.age) : '')
  const [sexInput, setSexInput] = useState<'male' | 'female'>((user.gender as 'male' | 'female') || 'male')
  const [weightInput, setWeightInput] = useState(user.weight ? String(user.weight) : '')
  const [heightInput, setHeightInput] = useState(user.height ? String(user.height) : '')
  const [objectiveInput, setObjectiveInput] = useState<FitnessObjective>(user.objective || 'maintenance')
  const [intensityInput, setIntensityInput] = useState<number>(user.aggressiveness_level || 2)

  const ageYears = ageInput ? Number(ageInput) : 0
  const sex = sexInput
  const weightKg = weightInput ? Number(weightInput) : undefined

  const biometricChanged = useMemo(() => {
    const currentAge = parseOptionalNumber(ageInput)
    const currentWeight = parseOptionalNumber(weightInput)
    const currentHeight = parseOptionalNumber(heightInput)

    return (
      currentAge !== (user.age ?? undefined) ||
      sexInput !== ((user.gender as 'male' | 'female') || 'male') ||
      currentWeight !== (user.weight ?? undefined) ||
      currentHeight !== (user.height ?? undefined)
    )
  }, [ageInput, sexInput, weightInput, heightInput, user.age, user.gender, user.weight, user.height])

  const objectiveChanged = useMemo(() => {
    return objectiveInput !== (user.objective || 'maintenance') || intensityInput !== (user.aggressiveness_level || 2)
  }, [objectiveInput, intensityInput, user.objective, user.aggressiveness_level])

  const isProfileDirty = biometricChanged || objectiveChanged

  const getSiteValue = (site: SiteKey): number | undefined => {
    if (!useTriplicate) {
      const raw = values[site].trim()
      if (!raw) return undefined
      return Number(raw)
    }

    const nums = triplicate[site]
      .map((v) => v.trim())
      .filter(Boolean)
      .map((v) => Number(v))

    if (nums.length === 0) return undefined
    const avg = nums.reduce((acc, cur) => acc + cur, 0) / nums.length
    return Number(avg.toFixed(2))
  }

  const skinfoldValidation = useMemo(() => {
    if (!ageYears || !sex) {
      return { canCalculate: false, message: 'Completa tu edad y sexo en la sección "Datos personales" primero.' }
    }

    const filledSites = SITES.filter((site) => {
      const value = getSiteValue(site.key)
      return value !== undefined && value > 0
    })

    const totalSites = SITES.length
    const filledCount = filledSites.length

    if (filledCount === 0) {
      return { canCalculate: false, message: 'Ingresa al menos los 7 pliegues cutáneos para calcular.' }
    }

    if (filledCount < totalSites) {
      const missing = totalSites - filledCount
      return { 
        canCalculate: false, 
        message: `Faltan ${missing} ${missing === 1 ? 'pliegue' : 'pliegues'} por completar. Se requieren los 7 para Jackson-Pollock 7 sitios.` 
      }
    }

    return { canCalculate: true, message: null }
  }, [ageYears, sex, values, triplicate, useTriplicate])

  useEffect(() => {
    setAgeInput(user.age ? String(user.age) : '')
    setSexInput((user.gender as 'male' | 'female') || 'male')
    setWeightInput(user.weight ? String(user.weight) : '')
    setHeightInput(user.height ? String(user.height) : '')
    setObjectiveInput(user.objective || 'maintenance')
    setIntensityInput(user.aggressiveness_level || 2)
  }, [user.age, user.gender, user.weight, user.height, user.objective, user.aggressiveness_level])

  useEffect(() => {
    loadHistory()
  }, [])

  const recommendedAgeWarning = useMemo(() => {
    if (!ageYears) return 'Completa tu edad en el perfil para mejorar la precisión del cálculo.'
    if (ageYears < 18 || ageYears > 61) {
      return 'Aviso: tu edad está fuera del rango clásico validado (18-61) para estas ecuaciones.'
    }
    return null
  }, [ageYears])

  const validateNumeric = (label: string, value: number | undefined): string | null => {
    if (value === undefined) return `${label} es obligatorio para JP7.`
    if (Number.isNaN(value)) return `${label} debe ser numérico.`
    if (value < 0 || value > 80) return `${label} debe estar entre 0 y 80 mm.`
    return null
  }

  async function loadHistory() {
    try {
      const data = await usersAPI.getSkinfoldHistory(10)
      setHistory(data)
    } catch {
      // silencioso para no contaminar UI
    }
  }

  const handleSavePersonalData = async () => {
    if (!isProfileDirty) return

    if (!ageInput || !weightInput || !heightInput) {
      showError('Edad, peso y altura son obligatorios.', 'Completa tus datos personales')
      return
    }

    const parsedAge = Number(ageInput)
    const parsedWeight = Number(weightInput)
    const parsedHeight = Number(heightInput)

    if (Number.isNaN(parsedAge) || parsedAge < 1 || parsedAge > 120) {
      showError('La edad debe estar entre 1 y 120 años.', 'Edad inválida')
      return
    }

    if (Number.isNaN(parsedWeight) || parsedWeight < 20 || parsedWeight > 300) {
      showError('El peso debe estar entre 20 y 300 kg.', 'Peso inválido')
      return
    }

    if (Number.isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 250) {
      showError('La altura debe estar entre 100 y 250 cm.', 'Altura inválida')
      return
    }

    if (!user.activity_level) {
      showError('Falta tu nivel de actividad. Revisa tu perfil base.', 'No se pudo guardar')
      return
    }

    setIsSavingProfile(true)
    try {
      if (biometricChanged) {
        await updateBiometrics({
          age: parsedAge,
          gender: sexInput,
          weight: parsedWeight,
          height: parsedHeight,
          activity_level: user.activity_level,
        })
      }

      if (objectiveChanged) {
        await updateObjective(objectiveInput, intensityInput)
      }

      showSuccess('Perfil actualizado', 'Recalculamos tu gasto calórico y objetivos con los nuevos datos')
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'No se pudieron guardar tus datos personales.'
      showError(String(detail), 'Error al guardar')
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handleCalculate = async () => {
    if (!ageYears || !sex) {
      showError('Faltan datos biométricos base (edad/sexo).', 'No se puede calcular')
      return
    }

    const payloadSites: SkinfoldValues = {}
    const validationErrors: string[] = []

    SITES.forEach(({ key, label }) => {
      const value = getSiteValue(key)
      const maybeError = validateNumeric(label, value)
      if (maybeError) validationErrors.push(maybeError)
      if (value !== undefined) {
        if (value > 60) {
          validationErrors.push(`${label}: valor alto (>60 mm), revisa técnica o repite medición.`)
        }
        payloadSites[key] = value
      }
    })

    const hardErrors = validationErrors.filter(
      (e) => e.includes('obligatorio') || e.includes('numérico') || e.includes('entre 0 y 80')
    )

    if (hardErrors.length > 0) {
      showError(hardErrors[0], 'Corrige los pliegues')
      return
    }

    setIsCalculating(true)
    try {
      const calculated = await usersAPI.calculateSkinfolds({
        sex,
        age_years: ageYears,
        weight_kg: weightKg,
        measurement_unit: 'mm',
        ...payloadSites,
      })
      setResult(calculated)
      await loadHistory()
      showSuccess('Cálculo completado', `${calculated.method}`)
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'No fue posible calcular. Verifica tus datos.'
      showError(String(detail), 'Error de cálculo')
    } finally {
      setIsCalculating(false)
    }
  }

  const handleSkinfoldTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    skinfoldTouchStartX.current = event.touches[0]?.clientX ?? null
  }

  const handleSkinfoldTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    if (skinfoldTouchStartX.current === null) return

    const endX = event.changedTouches[0]?.clientX ?? skinfoldTouchStartX.current
    const deltaX = endX - skinfoldTouchStartX.current
    const swipeThreshold = 45

    if (Math.abs(deltaX) < swipeThreshold) {
      skinfoldTouchStartX.current = null
      return
    }

    if (deltaX < 0) {
      setActiveSiteIndex((current) => Math.min(SITES.length - 1, current + 1))
    } else {
      setActiveSiteIndex((current) => Math.max(0, current - 1))
    }

    skinfoldTouchStartX.current = null
  }

  return (
    <section className="profile-panel">
      <div className="profile-tabs" role="tablist" aria-label="Secciones del perfil">
        <button
          type="button"
          className={`profile-tab profile-tab-personal ${activeSection === 'personal' ? 'active' : ''}`}
          role="tab"
          aria-selected={activeSection === 'personal'}
          onClick={() => setActiveSection('personal')}
        >
          <UserRound size={16} /> Datos personales
        </button>
        <button
          type="button"
          className={`profile-tab profile-tab-skinfolds ${activeSection === 'skinfolds' ? 'active' : ''}`}
          role="tab"
          aria-selected={activeSection === 'skinfolds'}
          onClick={() => setActiveSection('skinfolds')}
        >
          <Ruler size={16} /> Pliegues cutáneos
        </button>
      </div>

      {activeSection === 'personal' && (
        <article className="profile-section-card profile-section-card-personal">
          <div className="profile-biometric-grid profile-biometric-grid-editable profile-biometric-grid-compact">
            <div className="profile-biometric-item profile-biometric-box">
              <label className="profile-biometric-label"><CalendarDays size={16} /> Edad</label>
              <div className="profile-biometric-input-wrap">
                <input className="login-input" type="number" min={1} max={120} value={ageInput} onChange={(e) => setAgeInput(e.target.value)} />
                <span className="profile-biometric-unit">años</span>
              </div>
            </div>

            <div className="profile-biometric-item profile-biometric-box">
              <CustomSelect
                id="profile-gender"
                label="Sexo"
                labelIcon={<UserRound size={16} />}
                value={sexInput}
                onChange={(value) => setSexInput(value as 'male' | 'female')}
                options={[
                  { value: 'male', label: 'Masculino' },
                  { value: 'female', label: 'Femenino' },
                ]}
                placeholder="Selecciona"
              />
            </div>

            <div className="profile-biometric-item profile-biometric-box">
              <label className="profile-biometric-label"><Scale size={16} /> Peso</label>
              <div className="profile-biometric-input-wrap">
                <input className="login-input" type="number" min={20} max={300} step={0.1} value={weightInput} onChange={(e) => setWeightInput(e.target.value)} />
                <span className="profile-biometric-unit">kg</span>
              </div>
            </div>

            <div className="profile-biometric-item profile-biometric-box">
              <label className="profile-biometric-label"><Ruler size={16} /> Altura</label>
              <div className="profile-biometric-input-wrap">
                <input className="login-input" type="number" min={100} max={250} step={0.1} value={heightInput} onChange={(e) => setHeightInput(e.target.value)} />
                <span className="profile-biometric-unit">cm</span>
              </div>
            </div>

            <div className="profile-biometric-item profile-biometric-box">
              <CustomSelect
                id="profile-objective"
                label="Objetivo"
                labelIcon={<Target size={16} />}
                value={objectiveInput}
                onChange={(value) => setObjectiveInput(value as FitnessObjective)}
                options={OBJECTIVE_OPTIONS.map((option) => ({ value: option.value, label: option.label }))}
                placeholder="Selecciona objetivo"
              />
            </div>

            <div className="profile-biometric-item profile-biometric-box">
              <CustomSelect
                id="profile-intensity"
                label="Intensidad"
                labelIcon={<Flame size={16} />}
                value={String(intensityInput)}
                onChange={(value) => setIntensityInput(Number(value))}
                options={INTENSITY_OPTIONS.map((option) => ({ value: String(option.value), label: option.label }))}
                placeholder="Selecciona intensidad"
                panelPlacement="up"
              />
            </div>
          </div>

          <button
            type="button"
            className="login-button profile-save-button"
            onClick={handleSavePersonalData}
            disabled={isSavingProfile || !isProfileDirty}
          >
            <Save size={16} /> {isSavingProfile ? 'Guardando datos...' : isProfileDirty ? 'Guardar información' : 'Sin cambios para guardar'}
          </button>

          {recommendedAgeWarning && <p className="profile-warning">{recommendedAgeWarning}</p>}
        </article>
      )}

      {activeSection === 'skinfolds' && (
        <article className="profile-section-card">
          <div className="profile-toggle-card">
            <label className="profile-toggle">
              <input type="checkbox" checked={useTriplicate} onChange={(e) => setUseTriplicate(e.target.checked)} />
              <span className="profile-toggle-custom" aria-hidden="true"></span>
              <span className="profile-toggle-text">Usar 2-3 lecturas por sitio (promedio automático)</span>
            </label>
            <p className="profile-toggle-hint">Tip: con 3 tomas seguidas mejoras bastante la precisión 👌</p>
          </div>

          <div className="profile-skinfold-slider">
            <div className="profile-skinfold-slider-controls">
              <button
                type="button"
                className="profile-skinfold-nav"
                onClick={() => setActiveSiteIndex((current) => Math.max(0, current - 1))}
                disabled={activeSiteIndex === 0}
                aria-label="Ver pliegue anterior"
              >
                <ChevronLeft size={16} />
              </button>

              <p className="profile-skinfold-indicator">
                Sitio {activeSiteIndex + 1} de {SITES.length}
              </p>

              <button
                type="button"
                className="profile-skinfold-nav"
                onClick={() => setActiveSiteIndex((current) => Math.min(SITES.length - 1, current + 1))}
                disabled={activeSiteIndex === SITES.length - 1}
                aria-label="Ver siguiente pliegue"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div
              className="profile-skinfold-slider-window"
              aria-live="polite"
              onTouchStart={handleSkinfoldTouchStart}
              onTouchEnd={handleSkinfoldTouchEnd}
            >
              <div className="profile-skinfold-slider-track" style={{ transform: `translateX(-${activeSiteIndex * 100}%)` }}>
                {SITES.map((site) => (
                  <div key={site.key} className="profile-skinfold-slide">
                    <div className="profile-skinfold-card">
                      <label className="login-label profile-skinfold-site-label"><Ruler size={14} /> {site.label}</label>
                      <p className="profile-helper profile-skinfold-site-helper">{site.helper}</p>

                      {!useTriplicate ? (
                        <input
                          className="login-input profile-skinfold-input"
                          type="number"
                          min={0}
                          max={80}
                          step={0.1}
                          value={values[site.key]}
                          onChange={(e) => setValues((prev) => ({ ...prev, [site.key]: e.target.value }))}
                          placeholder="mm"
                        />
                      ) : (
                        <div className="profile-triplicate-row">
                          {[0, 1, 2].map((idx) => (
                            <input
                              key={idx}
                              className="login-input profile-skinfold-input"
                              type="number"
                              min={0}
                              max={80}
                              step={0.1}
                              value={triplicate[site.key][idx]}
                              onChange={(e) => {
                                setTriplicate((prev) => {
                                  const next = [...prev[site.key]] as [string, string, string]
                                  next[idx] = e.target.value
                                  return { ...prev, [site.key]: next }
                                })
                              }}
                              placeholder={`L${idx + 1}`}
                            />
                          ))}
                        </div>
                      )}

                      {useTriplicate && <p className="profile-avg">Promedio: {getSiteValue(site.key) ?? '-'} mm</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="profile-skinfold-dots" role="tablist" aria-label="Selector de pliegues">
              {SITES.map((site, index) => (
                <button
                  key={site.key}
                  type="button"
                  className={`profile-skinfold-dot ${index === activeSiteIndex ? 'active' : ''}`}
                  onClick={() => setActiveSiteIndex(index)}
                  aria-label={`Ir a ${site.label}`}
                  aria-current={index === activeSiteIndex}
                />
              ))}
            </div>
          </div>

          <button type="button" className="login-button profile-skinfold-calc-button" onClick={handleCalculate} disabled={isCalculating || !skinfoldValidation.canCalculate}>
            <Calculator size={16} /> {isCalculating ? 'Calculando...' : 'Calcular % grasa corporal'}
          </button>

          {!skinfoldValidation.canCalculate && skinfoldValidation.message && (
            <p className="profile-skinfold-validation-message">{skinfoldValidation.message}</p>
          )}

          {result && (
            <article className="profile-result-card profile-result-card-compact">
              <h3>Resultado</h3>
              <p><strong>% Grasa corporal:</strong> {result.body_fat_percent}%</p>
              <p><strong>% Masa libre:</strong> {result.fat_free_mass_percent}%</p>
              <p><strong>Suma pliegues:</strong> {result.sum_of_skinfolds_mm} mm</p>
              <p><strong>Método:</strong> {result.method}</p>
              <p className="profile-time"><CalendarClock size={14} /> {new Date(result.measured_at).toLocaleString('es-AR')}</p>
              {result.warnings.length > 0 && (
                <ul className="profile-warning-list">
                  {result.warnings.slice(0, 2).map((warning, index) => <li key={index}>{warning}</li>)}
                </ul>
              )}
            </article>
          )}

          {history.length > 0 && (
            <article className="profile-history-card profile-history-card-compact">
              <h3>Historial reciente</h3>
              {history.slice(0, 3).map((item) => (
                <div className="profile-history-item" key={`${item.measured_at}-${item.sum_of_skinfolds_mm}`}>
                  <div>
                    <p>{item.body_fat_percent}% grasa · {item.fat_free_mass_percent}% libre</p>
                    <small>{item.method}</small>
                  </div>
                  <span><Ruler size={12} /> {item.sum_of_skinfolds_mm} mm</span>
                </div>
              ))}
            </article>
          )}
        </article>
      )}
    </section>
  )
}

export default ProfileBiometricsPanel

import React, { useEffect, useState } from 'react'
import { Bone, Percent, Scale } from 'lucide-react'
import { SkinfoldCalculationResult } from '../services/api'

interface DashboardBodyCompositionProps {
  latestMeasurement: SkinfoldCalculationResult | null
  currentWeight?: number
  onWeightUpdate?: (newWeight: number) => Promise<void>
}

const DashboardBodyComposition: React.FC<DashboardBodyCompositionProps> = ({
  latestMeasurement,
  currentWeight,
  onWeightUpdate,
}) => {
  const [isEditingWeight, setIsEditingWeight] = useState(false)
  const [isSavingWeight, setIsSavingWeight] = useState(false)
  const [weightInput, setWeightInput] = useState(currentWeight !== undefined ? String(currentWeight) : '')
  const [weightError, setWeightError] = useState<string | null>(null)

  useEffect(() => {
    setWeightInput(currentWeight !== undefined ? String(currentWeight) : '')
  }, [currentWeight])

  const handleStartEditWeight = () => {
    setWeightError(null)
    setWeightInput(currentWeight !== undefined ? String(currentWeight) : '')
    setIsEditingWeight(true)
  }

  const handleCancelEditWeight = () => {
    setWeightError(null)
    setWeightInput(currentWeight !== undefined ? String(currentWeight) : '')
    setIsEditingWeight(false)
  }

  const handleSaveWeight = async () => {
    if (!onWeightUpdate) return

    const normalizedInput = weightInput.replace(',', '.').trim()
    const parsedWeight = Number(normalizedInput)

    if (!normalizedInput || Number.isNaN(parsedWeight)) {
      setWeightError('Ingresa un peso válido en kg.')
      return
    }

    if (parsedWeight < 20 || parsedWeight > 300) {
      setWeightError('El peso debe estar entre 20 y 300 kg.')
      return
    }

    setWeightError(null)
    setIsSavingWeight(true)

    try {
      await onWeightUpdate(Number(parsedWeight.toFixed(1)))
      setIsEditingWeight(false)
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'No pudimos actualizar el peso. Intenta de nuevo.'
      setWeightError(String(detail))
    } finally {
      setIsSavingWeight(false)
    }
  }

  if (!latestMeasurement) {
    return (
      <section className="dashboard-body-comp-card" aria-label="Composición corporal">
        <header className="dashboard-body-comp-header">
          <h3>Composición corporal</h3>
          <p>Sin medición aún. Cárgala en Perfil → Pliegues cutáneos.</p>
        </header>
      </section>
    )
  }

  return (
    <section className="dashboard-body-comp-card" aria-label="Composición corporal">
      <header className="dashboard-body-comp-header">
        <h3>Composición corporal</h3>
        <p>Última medición: {new Date(latestMeasurement.measured_at).toLocaleDateString('es-AR')}</p>
      </header>

      <div className="dashboard-body-comp-stack">
        {currentWeight !== undefined && currentWeight !== null && (
          <article className="dashboard-body-comp-item weight">
            <div className="dashboard-body-comp-icon" aria-hidden="true">
              <Scale size={14} />
            </div>
            <div className="dashboard-body-comp-text">
              <p className="dashboard-body-comp-label">Peso</p>
              {isEditingWeight ? (
                <div className="dashboard-body-comp-weight-editor">
                  <input
                    type="number"
                    min={20}
                    max={300}
                    step={0.1}
                    value={weightInput}
                    onChange={(event) => setWeightInput(event.target.value)}
                    className="dashboard-body-comp-weight-input"
                    aria-label="Actualizar peso en kg"
                  />
                  <span className="dashboard-body-comp-unit">kg</span>
                </div>
              ) : (
                <p className="dashboard-body-comp-value">{currentWeight} kg</p>
              )}
              {weightError && <p className="dashboard-body-comp-error">{weightError}</p>}
            </div>

            <div className="dashboard-body-comp-actions">
              {!isEditingWeight ? (
                <button type="button" className="dashboard-body-comp-btn" onClick={handleStartEditWeight}>
                  Actualizar
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="dashboard-body-comp-btn primary"
                    onClick={handleSaveWeight}
                    disabled={isSavingWeight}
                  >
                    {isSavingWeight ? 'Guardando...' : 'Guardar'}
                  </button>
                  <button
                    type="button"
                    className="dashboard-body-comp-btn ghost"
                    onClick={handleCancelEditWeight}
                    disabled={isSavingWeight}
                  >
                    Cancelar
                  </button>
                </>
              )}
            </div>
          </article>
        )}

        <article className="dashboard-body-comp-item fat">
          <div className="dashboard-body-comp-icon" aria-hidden="true">
            <Percent size={14} />
          </div>
          <div className="dashboard-body-comp-text">
            <p className="dashboard-body-comp-label">% Grasa corporal</p>
            <p className="dashboard-body-comp-value">{latestMeasurement.body_fat_percent}%</p>
          </div>
        </article>

        <article className="dashboard-body-comp-item lean">
          <div className="dashboard-body-comp-icon" aria-hidden="true">
            <Bone size={14} />
          </div>
          <div className="dashboard-body-comp-text">
            <p className="dashboard-body-comp-label">Masa magra</p>
            <p className="dashboard-body-comp-value">{latestMeasurement.fat_free_mass_percent}%</p>
          </div>
        </article>
      </div>
    </section>
  )
}

export default DashboardBodyComposition
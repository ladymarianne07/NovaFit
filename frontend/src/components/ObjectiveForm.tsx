import React, { useState } from 'react'
import { Target, TrendingUp, ArrowLeft } from 'lucide-react'
import { FitnessObjective } from '../services/api'
import '../styles/globals.css'

/**
 * Props for ObjectiveForm component
 * @interface ObjectiveFormProps
 * @property {FitnessObjective} [selectedObjective] - Currently selected fitness objective
 * @property {number} [selectedAggressiveness] - Currently selected aggressiveness level (1-3), defaults to 2
 * @property {Function} onObjectiveChange - Callback when objective or aggressiveness changes
 */
interface ObjectiveFormProps {
  selectedObjective?: FitnessObjective
  selectedAggressiveness?: number
  onObjectiveChange: (objective: FitnessObjective, aggressiveness: number) => void
}

/**
 * ObjectiveForm Component - Two-stage wizard for fitness objective selection
 * 
 * Stage 1: User selects from 5 fitness objectives (maintenance, fat_loss, muscle_gain, body_recomp, performance)
 * Stage 2: User selects aggressiveness level (1=Conservative, 2=Moderate, 3=Aggressive)
 * 
 * The component automatically advances from stage 1 to stage 2 after objective selection.
 * Users can navigate back to change their objective selection.
 * 
 * @component
 * @example
 * const [objective, setObjective] = useState<FitnessObjective>('muscle_gain')
 * const [agg, setAgg] = useState(2)
 * return (
 *   <ObjectiveForm
 *     selectedObjective={objective}
 *     selectedAggressiveness={agg}
 *     onObjectiveChange={(obj, aggLevel) => {
 *       setObjective(obj)
 *       setAgg(aggLevel)
 *     }}
 *   />
 * )
 */
const ObjectiveForm: React.FC<ObjectiveFormProps> = ({
  selectedObjective,
  selectedAggressiveness = 2,
  onObjectiveChange
}) => {
  const [objective, setObjective] = useState<FitnessObjective | undefined>(selectedObjective)
  const [aggressiveness, setAggressiveness] = useState(selectedAggressiveness)
  const [stage, setStage] = useState<'objective' | 'aggressiveness'>(
    selectedObjective ? 'aggressiveness' : 'objective'
  )

  // Objective metadata for display
  const objectiveMetadata: Record<FitnessObjective, {
    label: string
    description: string
  }> = {
    maintenance: {
      label: 'Mantenimiento',
      description: 'Mantén tu peso actual'
    },
    fat_loss: {
      label: 'Pérdida de Grasa',
      description: 'Reduce peso de manera controlada'
    },
    muscle_gain: {
      label: 'Ganancia Muscular',
      description: 'Construye músculo magro'
    },
    body_recomp: {
      label: 'Recomposición Corporal',
      description: 'Pierde grasa y gana músculo'
    },
    performance: {
      label: 'Rendimiento Atlético',
      description: 'Optimiza para el desempeño'
    }
  }

  const aggressivenessLabels = {
    1: 'Conservador',
    2: 'Moderado',
    3: 'Agresivo'
  } as const

  const handleObjectiveChange = (newObjective: FitnessObjective) => {
    setObjective(newObjective)
    onObjectiveChange(newObjective, aggressiveness)
    setStage('aggressiveness')
  }

  const handleAggressivenessChange = (level: number) => {
    if (!objective) {
      return
    }

    setAggressiveness(level)
    onObjectiveChange(objective, level)
  }

  const aggressivenessDescription = {
    1: 'Avance gradual y sostenible.',
    2: 'Balance óptimo entre progreso y consistencia.',
    3: 'Ritmo intenso para resultados más rápidos.'
  } as const

  return (
    <div className="objective-form">
      <div className="objective-wizard-card">
        {stage === 'objective' && (
          <>
            <label className="form-label objective-step-title">
              <Target size={18} className="objective-step-title-icon" />
              Elige tu objetivo
            </label>
            <p className="selector-hint">Selecciona una opción para continuar al nivel de intensidad.</p>

            <div className="objectives-grid compact">
              {(Object.keys(objectiveMetadata) as FitnessObjective[]).map((obj) => (
                <button
                  key={obj}
                  type="button"
                  className={`objective-card objective-card--${obj} ${objective === obj ? 'active' : ''}`}
                  onClick={() => handleObjectiveChange(obj)}
                >
                  <div className="objective-card-header">
                    <span className={`objective-label objective-label--${obj}`}>{objectiveMetadata[obj].label}</span>
                  </div>
                  <p className="objective-description">{objectiveMetadata[obj].description}</p>
                </button>
              ))}
            </div>
          </>
        )}

        {stage === 'aggressiveness' && objective && (
          <>
            <div className="objective-step-header">
              <button
                type="button"
                className="objective-back-button"
                onClick={() => setStage('objective')}
              >
                <ArrowLeft size={16} />
                Cambiar objetivo
              </button>

              <div className={`objective-selected-chip objective-selected-chip--${objective}`}>
                {objectiveMetadata[objective].label}
              </div>
            </div>

            <label className="form-label objective-step-title">
              <TrendingUp size={18} className="objective-step-title-icon" />
              Nivel de intensidad
            </label>
            <p className="selector-hint">Elige qué tan rápido quieres avanzar.</p>

            <div className="aggressiveness-options compact">
              {([1, 2, 3] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`aggressiveness-btn ${aggressiveness === level ? 'active' : ''}`}
                  onClick={() => handleAggressivenessChange(level)}
                >
                  <span className="aggressiveness-number">{level}</span>
                  <span className="aggressiveness-name">{aggressivenessLabels[level]}</span>
                </button>
              ))}
            </div>

            <div className="delta-info compact">
              <p>{aggressivenessDescription[aggressiveness as 1 | 2 | 3]}</p>
            </div>
          </>
        )}
      </div>

    </div>
  )
}

export default ObjectiveForm

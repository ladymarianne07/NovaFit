import React, { useState, useEffect } from 'react'
import { Target, TrendingUp, TrendingDown } from 'lucide-react'
import {FitnessObjective } from '../services/api'
import { Button } from './UI/Button'
import '../styles/globals.css'

interface ObjectiveFormProps {
  selectedObjective?: FitnessObjective
  selectedAggressiveness?: number
  tdee: number
  weight: number
  onObjectiveChange: (objective: FitnessObjective, aggressiveness: number) => void
  loading?: boolean
}

interface TargetCalcuation {
  target_calories: number
  protein_g: number
  fat_g: number
  carbs_g: number
}

const ObjectiveForm: React.FC<ObjectiveFormProps> = ({
  selectedObjective,
  selectedAggressiveness = 2,
  tdee,
  weight,
  onObjectiveChange,
  loading = false
}) => {
  const [objective, setObjective] = useState<FitnessObjective>(selectedObjective || 'maintenance')
  const [aggressiveness, setAggressiveness] = useState(selectedAggressiveness)
  const [targets, setTargets] = useState<TargetCalcuation | null>(null)

  // Objective metadata for display
  const objectiveMetadata: Record<FitnessObjective, {
    label: string
    description: string
    color: string
    supportedLevels: boolean
  }> = {
    maintenance: {
      label: 'Mantenimiento',
      description: 'Mantén tu peso actual',
      color: '#3b82f6',
      supportedLevels: false
    },
    fat_loss: {
      label: 'Pérdida de Grasa',
      description: 'Reduce peso de manera controlada',
      color: '#ef4444',
      supportedLevels: true
    },
    muscle_gain: {
      label: 'Ganancia Muscular',
      description: 'Construye músculo magro',
      color: '#10b981',
      supportedLevels: true
    },
    body_recomp: {
      label: 'Recomposición Corporal',
      description: 'Pierde grasa y gana músculo',
      color: '#f59e0b',
      supportedLevels: true
    },
    performance: {
      label: 'Rendimiento Atlético',
      description: 'Optimiza para el desempeño',
      color: '#8b5cf6',
      supportedLevels: false
    }
  }

  const aggressivenessLabels = {
    1: 'Conservador',
    2: 'Moderado',
    3: 'Agresivo'
  } as const

  // Calculate targets whenever objective or aggressiveness changes
  useEffect(() => {
    calculateTargets()
  }, [objective, aggressiveness])

  const calculateTargets = () => {
    // Calorie delta by objective and aggressiveness
    const deltaMap: Record<FitnessObjective, Record<number, number>> = {
      maintenance: { 1: 0, 2: 0, 3: 0 },
      fat_loss: { 1: -0.15, 2: -0.20, 3: -0.25 },
      muscle_gain: { 1: 0.05, 2: 0.10, 3: 0.15 },
      body_recomp: { 1: 0.00, 2: -0.05, 3: -0.10 },
      performance: { 1: 0, 2: 0, 3: 0.05 }
    }

    const proteinFactors: Record<FitnessObjective, number> = {
      maintenance: 1.6,
      fat_loss: 2.0,
      muscle_gain: 1.8,
      body_recomp: 2.0,
      performance: 1.6
    }

    const fatPercents: Record<FitnessObjective, number> = {
      maintenance: 0.30,
      fat_loss: 0.25,
      muscle_gain: 0.25,
      body_recomp: 0.25,
      performance: 0.25
    }

    // Calculate target calories
    const delta = deltaMap[objective][aggressiveness]
    const target_calories = Math.round(tdee * (1 + delta))

    // Calculate macros
    const protein_g = Math.round(weight * proteinFactors[objective])
    const protein_kcal = protein_g * 4

    const fat_percent = fatPercents[objective]
    const fat_kcal = Math.round(target_calories * fat_percent)
    const fat_g = Math.round(fat_kcal / 9)

    let carb_kcal = target_calories - protein_kcal - fat_kcal

    // Handle negative carbs
    if (carb_kcal < 0) {
      const min_fat_kcal = Math.round(target_calories * 0.20)
      carb_kcal = target_calories - protein_kcal - min_fat_kcal
    }

    const carbs_g = Math.round(carb_kcal / 4)

    setTargets({
      target_calories,
      protein_g,
      fat_g,
      carbs_g
    })
  }

  const handleObjectiveChange = (newObjective: FitnessObjective) => {
    setObjective(newObjective)
    const newAggressiveness = objectiveMetadata[newObjective].supportedLevels ? aggressiveness : 2
    setAggressiveness(newAggressiveness)
    onObjectiveChange(newObjective, newAggressiveness)
  }

  const handleAggressivenessChange = (level: number) => {
    setAggressiveness(level)
    onObjectiveChange(objective, level)
  }

  const meta = objectiveMetadata[objective]

  return (
    <div className="objective-form">
      {/* Objetivo Selection */}
      <div className="objective-selection-container">
        <label className="form-label">
          <Target size={18} style={{ marginRight: '8px' }} />
          Objetivo Fitness
        </label>
        
        <div className="objectives-grid">
          {(Object.keys(objectiveMetadata) as FitnessObjective[]).map((obj) => (
            <button
              key={obj}
              className={`objective-card ${objective === obj ? 'active' : ''}`}
              onClick={() => handleObjectiveChange(obj)}
              style={{
                borderColor: objective === obj ? objectiveMetadata[obj].color : '#e5e7eb'
              }}
            >
              <div className="objective-card-header">
                <span className="objective-label">{objectiveMetadata[obj].label}</span>
              </div>
              <p className="objective-description">{objectiveMetadata[obj].description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Aggressiveness Selector (only for objectives that support it) */}
      {meta.supportedLevels && (
        <div className="aggressiveness-selector">
          <label className="form-label">
            <TrendingUp size={18} style={{ marginRight: '8px' }} />
            Intensidad
          </label>
          <p className="selector-hint">Ajusta la intensidad de tu objetivo</p>
          
          <div className="aggressiveness-options">
            {([1, 2, 3] as const).map((level) => (
              <button
                key={level}
                className={`aggressiveness-btn ${aggressiveness === level ? 'active' : ''}`}
                onClick={() => handleAggressivenessChange(level)}
              >
                <span className="aggressiveness-number">{level}</span>
                <span className="aggressiveness-name">{aggressivenessLabels[level]}</span>
              </button>
            ))}
          </div>

          {/* Delta explanation */}
          <div className="delta-info">
            {objective === 'fat_loss' && aggressiveness === 1 && (
              <p>Déficit del 15% - Pérdida gradual y sostenible</p>
            )}
            {objective === 'fat_loss' && aggressiveness === 2 && (
              <p>Déficit del 20% - Balance entre velocidad y sostenibilidad</p>
            )}
            {objective === 'fat_loss' && aggressiveness === 3 && (
              <p>Déficit del 25% - Pérdida rápida (requiere entrenamiento)</p>
            )}
            {objective === 'muscle_gain' && aggressiveness === 1 && (
              <p>Superávit del 5% - Ganancia lenta y controlada</p>
            )}
            {objective === 'muscle_gain' && aggressiveness === 2 && (
              <p>Superávit del 10% - Ganancia óptima de músculo</p>
            )}
            {objective === 'muscle_gain' && aggressiveness === 3 && (
              <p>Superávit del 15% - Ganancia rápida (más grasa)</p>
            )}
            {objective === 'body_recomp' && aggressiveness === 1 && (
              <p>Mantenimiento - Cambio lento</p>
            )}
            {objective === 'body_recomp' && aggressiveness === 2 && (
              <p>Déficit del 5% - Balance óptimo</p>
            )}
            {objective === 'body_recomp' && aggressiveness === 3 && (
              <p>Déficit del 10% - Mayor pérdida de grasa</p>
            )}
          </div>
        </div>
      )}

      {/* Targets Display */}
      {targets && (
        <div className="targets-display">
          <h3 className="targets-title">Tus Objetivos Diarios</h3>
          
          <div className="targets-grid">
            {/* TDEE */}
            <div className="target-card">
              <div className="target-label">Mantenimiento (TDEE)</div>
              <div className="target-value">{Math.round(tdee)}</div>
              <div className="target-unit">kcal</div>
            </div>

            {/* Target Calories */}
            <div className="target-card highlight">
              <div className="target-label">
                {targets.target_calories > tdee ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <TrendingUp size={14} style={{ color: '#10b981' }} />
                    Objetivo
                  </div>
                ) : targets.target_calories < tdee ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <TrendingDown size={14} style={{ color: '#ef4444' }} />
                    Objetivo
                  </div>
                ) : (
                  'Objetivo'
                )}
              </div>
              <div className="target-value" style={{ color: meta.color }}>
                {targets.target_calories}
              </div>
              <div className="target-unit">kcal</div>
            </div>
          </div>

          {/* Macronutrient Targets */}
          <div className="macros-display">
            <h4 className="macros-title">Macronutrientes</h4>
            
            <div className="macros-grid">
              <div className="macro-target">
                <div className="macro-name">Proteína</div>
                <div className="macro-value">{targets.protein_g}g</div>
                <div className="macro-kcal">{targets.protein_g * 4} kcal</div>
              </div>

              <div className="macro-target">
                <div className="macro-name">Grasa</div>
                <div className="macro-value">{targets.fat_g}g</div>
                <div className="macro-kcal">{targets.fat_g * 9} kcal</div>
              </div>

              <div className="macro-target">
                <div className="macro-name">Carbohidratos</div>
                <div className="macro-value">{targets.carbs_g}g</div>
                <div className="macro-kcal">{targets.carbs_g * 4} kcal</div>
              </div>
            </div>
          </div>

          {/* Calorie adjustment info */}
          {targets.target_calories !== tdee && (
            <div className="adjustment-info">
              <p>
                {targets.target_calories > tdee 
                  ? `+${targets.target_calories - Math.round(tdee)} kcal`
                  : `${targets.target_calories - Math.round(tdee)} kcal`
                } desde tu mantenimiento
              </p>
            </div>
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="loading-indicator">
          Calculando objetivos...
        </div>
      )}
    </div>
  )
}

export default ObjectiveForm

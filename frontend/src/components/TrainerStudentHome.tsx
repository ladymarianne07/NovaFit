/**
 * TrainerStudentHome - Trainer view of a student's daily dashboard.
 * Shows the shared student selector at the top, then renders the selected
 * student's macronutrient overview and body composition (same as the student's Home tab).
 */
import React, { useEffect, useState } from 'react'
import { ChevronDown, Users, UserRound } from 'lucide-react'
import { MacronutrientData, SkinfoldCalculationResult, StudentSummary, trainerAPI } from '../services/api'
import DashboardNutritionOverview from './DashboardNutritionOverview'
import DashboardBodyComposition from './DashboardBodyComposition'

interface TrainerStudentHomeProps {
  students: StudentSummary[]
  selectedStudentId: number | null
  onStudentSelect: (id: number | null) => void
}

const TrainerStudentHome: React.FC<TrainerStudentHomeProps> = ({
  students,
  selectedStudentId,
  onStudentSelect,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [macroData, setMacroData] = useState<MacronutrientData | null>(null)
  const [skinfold, setSkinfold] = useState<SkinfoldCalculationResult | null>(null)
  const [loadingData, setLoadingData] = useState(false)

  const selectedStudent = students.find((s) => s.id === selectedStudentId) ?? null

  const studentName = selectedStudent
    ? (`${selectedStudent.first_name ?? ''} ${selectedStudent.last_name ?? ''}`).trim() || selectedStudent.email
    : null

  useEffect(() => {
    if (!selectedStudentId) {
      setMacroData(null)
      setSkinfold(null)
      return
    }

    setLoadingData(true)
    const today = new Date()
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

    Promise.all([
      trainerAPI.getStudentMacros(selectedStudentId, dateStr),
      trainerAPI.getStudentSkinfolds(selectedStudentId, 1),
    ])
      .then(([macros, skinfolds]) => {
        setMacroData(macros)
        setSkinfold(skinfolds[0] ?? null)
      })
      .catch(() => {
        setMacroData(null)
        setSkinfold(null)
      })
      .finally(() => setLoadingData(false))
  }, [selectedStudentId])

  return (
    <section className="dashboard-main-stack" aria-label="Panel de alumno — Inicio">
      {/* Student selector */}
      <div className="trainer-dashboard-selector-wrap">
        <p className="trainer-dashboard-selector-label">
          <Users size={14} /> Ver alumno
        </p>
        <div className="trainer-dashboard-selector">
          <button
            type="button"
            className="trainer-dashboard-selector-btn"
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-haspopup="listbox"
            aria-expanded={dropdownOpen}
          >
            <span>{studentName ?? 'Seleccioná un alumno'}</span>
            <ChevronDown size={16} />
          </button>

          {dropdownOpen && (
            <ul className="trainer-dashboard-selector-list" role="listbox" aria-label="Lista de alumnos">
              {students.map((student) => {
                const name = (`${student.first_name ?? ''} ${student.last_name ?? ''}`).trim() || student.email
                return (
                  <li key={student.id} role="option" aria-selected={student.id === selectedStudentId}>
                    <button
                      type="button"
                      className={`trainer-dashboard-selector-option ${student.id === selectedStudentId ? 'selected' : ''}`}
                      onClick={() => {
                        onStudentSelect(student.id)
                        setDropdownOpen(false)
                      }}
                    >
                      {name}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>

      {/* Content */}
      {!selectedStudent ? (
        <section className="dashboard-placeholder-card">
          <div className="loading-stack">
            <UserRound size={36} strokeWidth={1.5} style={{ opacity: 0.35 }} />
            <h2>Seleccioná un alumno</h2>
            <p>Elegí un alumno del selector para ver su resumen del día.</p>
          </div>
        </section>
      ) : loadingData ? (
        <section className="dashboard-placeholder-card">
          <div className="loading-stack">
            <div className="neon-loader neon-loader--md" aria-hidden="true" />
            <h2>Cargando datos de {studentName}</h2>
          </div>
        </section>
      ) : macroData ? (
        <div className="dashboard-overview-wrap">
          <DashboardNutritionOverview
            currentCalories={Math.round(macroData.total_calories)}
            targetCalories={Math.round(macroData.calories_target)}
            macroData={macroData}
            calorieMode="intake"
            exerciseCalories={0}
            macroTargetPercentages={{
              carbs: macroData.carbs_percentage,
              protein: macroData.protein_percentage,
              fat: macroData.fat_percentage,
            }}
          />
          <DashboardBodyComposition
            latestMeasurement={skinfold}
            currentWeight={selectedStudent.weight_kg ?? undefined}
          />
        </div>
      ) : (
        <section className="dashboard-placeholder-card">
          <div className="loading-stack">
            <UserRound size={32} strokeWidth={1.5} style={{ opacity: 0.35 }} />
            <h2>Sin datos por hoy</h2>
            <p>{studentName} no registró comidas hoy todavía.</p>
          </div>
        </section>
      )}
    </section>
  )
}

export default TrainerStudentHome

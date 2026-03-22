/**
 * TrainerStudentsModule - Student list or selected student's progress view.
 * When no student is selected: shows the linked students list.
 * When a student is selected: shows their skinfold history and biometric summary.
 */
import React, { useEffect, useState } from 'react'
import { CalendarClock, ChevronDown, Ruler, UserPlus, Users, UserRound } from 'lucide-react'
import { SkinfoldCalculationResult, StudentSummary, trainerAPI } from '../services/api'

interface TrainerStudentsModuleProps {
  students: StudentSummary[]
  selectedStudentId: number | null
  onStudentSelect: (id: number | null) => void
}

const TrainerStudentsModule: React.FC<TrainerStudentsModuleProps> = ({
  students,
  selectedStudentId,
  onStudentSelect,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [skinfolds, setSkinfolds] = useState<SkinfoldCalculationResult[]>([])
  const [loadingSkinfolds, setLoadingSkinfolds] = useState(false)

  const selectedStudent = students.find((s) => s.id === selectedStudentId) ?? null

  const studentName = selectedStudent
    ? (`${selectedStudent.first_name ?? ''} ${selectedStudent.last_name ?? ''}`).trim() || selectedStudent.email
    : null

  useEffect(() => {
    if (!selectedStudentId) {
      setSkinfolds([])
      return
    }
    setLoadingSkinfolds(true)
    trainerAPI.getStudentSkinfolds(selectedStudentId, 5)
      .then(setSkinfolds)
      .catch(() => setSkinfolds([]))
      .finally(() => setLoadingSkinfolds(false))
  }, [selectedStudentId])

  if (students.length === 0) {
    return (
      <section className="dashboard-placeholder-card" aria-label="Sin alumnos vinculados">
        <div className="loading-stack">
          <UserPlus size={40} strokeWidth={1.5} style={{ opacity: 0.4 }} />
          <h2>Sin alumnos vinculados</h2>
          <p>Generá un código de invitación desde tu perfil y compartilo con tus alumnos.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="dashboard-main-stack" aria-label="Alumnos">
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
        /* No student selected — show the student list */
        <div>
          <div className="trainer-students-header">
            <Users size={16} />
            <span>{students.length} {students.length === 1 ? 'alumno vinculado' : 'alumnos vinculados'}</span>
          </div>
          <ul className="trainer-students-list">
            {students.map((student) => (
              <li key={student.id} className="trainer-student-card">
                <div className="trainer-student-avatar" aria-hidden="true">
                  {(student.first_name?.[0] ?? student.email[0]).toUpperCase()}
                </div>
                <div className="trainer-student-info">
                  <p className="trainer-student-name">
                    {student.first_name && student.last_name
                      ? `${student.first_name} ${student.last_name}`
                      : student.email}
                  </p>
                  <p className="trainer-student-email">{student.email}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : loadingSkinfolds ? (
        <section className="dashboard-placeholder-card">
          <div className="loading-stack">
            <div className="neon-loader neon-loader--md" aria-hidden="true" />
            <h2>Cargando progreso de {studentName}</h2>
          </div>
        </section>
      ) : skinfolds.length === 0 ? (
        <section className="dashboard-placeholder-card">
          <div className="loading-stack">
            <Ruler size={32} strokeWidth={1.5} style={{ opacity: 0.35 }} />
            <h2>Sin mediciones registradas</h2>
            <p>{studentName} no tiene pliegues cutáneos guardados todavía.</p>
          </div>
        </section>
      ) : (
        <article className="profile-history-card profile-history-card-compact">
          <div className="trainer-students-header">
            <Ruler size={16} />
            <span>Historial de pliegues — {studentName}</span>
          </div>
          {skinfolds.map((item) => (
            <div className="profile-history-item" key={`${item.measured_at}-${item.sum_of_skinfolds_mm}`}>
              <div>
                <p>{item.body_fat_percent}% grasa · {item.fat_free_mass_percent}% libre</p>
                <small>{item.method}</small>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                <span><Ruler size={12} /> {item.sum_of_skinfolds_mm} mm</span>
                <span style={{ fontSize: '0.7rem', opacity: 0.5 }}>
                  <CalendarClock size={10} /> {new Date(item.measured_at).toLocaleDateString('es-AR')}
                </span>
              </div>
            </div>
          ))}
        </article>
      )}
    </section>
  )
}

export default TrainerStudentsModule

import React, { useEffect, useState } from 'react'
import { UserPlus, Users, ChevronDown } from 'lucide-react'
import { trainerAPI, StudentSummary } from '../services/api'

const TrainerEmptyDashboard: React.FC = () => {
  const [students, setStudents] = useState<StudentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null)
  const [dropdownOpen, setDropdownOpen] = useState(false)

  useEffect(() => {
    trainerAPI.listStudents()
      .then(setStudents)
      .catch(() => setStudents([]))
      .finally(() => setLoading(false))
  }, [])

  const selectedStudent = students.find((s) => s.id === selectedStudentId) ?? null

  if (loading) {
    return (
      <section className="dashboard-placeholder-card">
        <div className="loading-stack">
          <div className="neon-loader neon-loader--md" aria-hidden="true" />
          <h2>Cargando alumnos</h2>
        </div>
      </section>
    )
  }

  if (students.length === 0) {
    return (
      <section className="dashboard-placeholder-card" aria-label="Sin alumnos vinculados">
        <div className="loading-stack">
          <UserPlus size={40} strokeWidth={1.5} style={{ opacity: 0.4 }} />
          <h2>Sin alumnos vinculados</h2>
          <p>Generá un código de invitación desde tu perfil y compartilo con tus alumnos para empezar a ver su progreso aquí.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="dashboard-main-stack" aria-label="Panel de entrenador">
      {/* Student selector */}
      <div className="trainer-dashboard-selector-wrap">
        <p className="trainer-dashboard-selector-label">
          <Users size={14} /> Ver panel de alumno
        </p>

        <div className="trainer-dashboard-selector" style={{ position: 'relative' }}>
          <button
            type="button"
            className="trainer-dashboard-selector-btn"
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-haspopup="listbox"
            aria-expanded={dropdownOpen}
          >
            <span>{selectedStudent ? `${selectedStudent.first_name ?? ''} ${selectedStudent.last_name ?? ''}`.trim() || selectedStudent.email : 'Seleccioná un alumno'}</span>
            <ChevronDown size={16} />
          </button>

          {dropdownOpen && (
            <ul
              className="trainer-dashboard-selector-list"
              role="listbox"
              aria-label="Lista de alumnos"
            >
              {students.map((student) => {
                const name = `${student.first_name ?? ''} ${student.last_name ?? ''}`.trim() || student.email
                return (
                  <li key={student.id} role="option" aria-selected={student.id === selectedStudentId}>
                    <button
                      type="button"
                      className={`trainer-dashboard-selector-option ${student.id === selectedStudentId ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedStudentId(student.id)
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

      {/* Placeholder until student data loading is implemented */}
      <section className="dashboard-placeholder-card dashboard-placeholder-card-plain">
        <div className="loading-stack">
          <Users size={32} strokeWidth={1.5} style={{ opacity: 0.35 }} />
          {selectedStudent ? (
            <>
              <h2>
                {`${selectedStudent.first_name ?? ''} ${selectedStudent.last_name ?? ''}`.trim() || selectedStudent.email}
              </h2>
              <p>El panel detallado del alumno estará disponible próximamente.</p>
            </>
          ) : (
            <>
              <h2>Seleccioná un alumno</h2>
              <p>Elegí un alumno del selector para ver su información.</p>
            </>
          )}
        </div>
      </section>
    </section>
  )
}

export default TrainerEmptyDashboard

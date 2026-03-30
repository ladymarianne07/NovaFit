import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import BottomNavigation from '../components/BottomNavigation'

describe('BottomNavigation - role-based tabs', () => {
  test('renders student tabs by default (no role prop)', () => {
    render(<BottomNavigation />)
    expect(screen.getByRole('button', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /comidas/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entreno/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /progreso/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /alumnos/i })).not.toBeInTheDocument()
  })

  test('renders student tabs when role is student', () => {
    render(<BottomNavigation role="student" />)
    expect(screen.getByRole('button', { name: /comidas/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entreno/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /progreso/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /alumnos/i })).not.toBeInTheDocument()
  })

  test('renders trainer tabs when role is trainer', () => {
    render(<BottomNavigation role="trainer" />)
    expect(screen.getByRole('button', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /alumnos/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /comidas/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /entreno/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /progreso/i })).not.toBeInTheDocument()
  })

  test('marks the active tab correctly for student', () => {
    render(<BottomNavigation role="student" activeTab="meals" />)
    expect(screen.getByRole('button', { name: /comidas/i })).toHaveClass('active')
    expect(screen.getByRole('button', { name: /home/i })).not.toHaveClass('active')
  })

  test('marks the active tab correctly for trainer', () => {
    render(<BottomNavigation role="trainer" activeTab="students" />)
    expect(screen.getByRole('button', { name: /alumnos/i })).toHaveClass('active')
    expect(screen.getByRole('button', { name: /home/i })).not.toHaveClass('active')
  })

  test('calls onTabChange with correct tab id on student nav', () => {
    const onTabChange = jest.fn()
    render(<BottomNavigation role="student" onTabChange={onTabChange} />)
    fireEvent.click(screen.getByRole('button', { name: /progreso/i }))
    expect(onTabChange).toHaveBeenCalledWith('progress')
  })

  test('calls onTabChange with students when trainer clicks Alumnos', () => {
    const onTabChange = jest.fn()
    render(<BottomNavigation role="trainer" onTabChange={onTabChange} />)
    fireEvent.click(screen.getByRole('button', { name: /alumnos/i }))
    expect(onTabChange).toHaveBeenCalledWith('students')
  })
})

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ThemePickerModal from '../components/ThemePickerModal'
import { ThemeProvider } from '../contexts/ThemeContext'

// localStorage is a jest mock (see src/test/setup.ts)
const mockSetItem = localStorage.setItem as jest.Mock

const renderWithTheme = (ui: React.ReactElement) =>
  render(<ThemeProvider>{ui}</ThemeProvider>)

describe('ThemePickerModal', () => {
  beforeEach(() => {
    mockSetItem.mockClear()
    document.documentElement.removeAttribute('data-theme')
    ;(localStorage.getItem as jest.Mock).mockReturnValue(null)
  })

  test('renders three theme options', () => {
    renderWithTheme(<ThemePickerModal />)
    expect(screen.getByText('Original')).toBeInTheDocument()
    expect(screen.getByText('Dark Mode')).toBeInTheDocument()
    expect(screen.getByText('Light Mode')).toBeInTheDocument()
  })

  test('renders the confirm button with current theme name', () => {
    renderWithTheme(<ThemePickerModal />)
    expect(screen.getByRole('button', { name: /continuar con original/i })).toBeInTheDocument()
  })

  test('selecting Dark Mode updates the confirm button label', () => {
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByText('Dark Mode'))
    expect(screen.getByRole('button', { name: /continuar con dark mode/i })).toBeInTheDocument()
  })

  test('selecting Light Mode updates the confirm button label', () => {
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByText('Light Mode'))
    expect(screen.getByRole('button', { name: /continuar con light mode/i })).toBeInTheDocument()
  })

  test('clicking confirm saves nova_theme_chosen to localStorage', () => {
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByRole('button', { name: /continuar con original/i }))
    expect(mockSetItem).toHaveBeenCalledWith('nova_theme_chosen', '1')
  })

  test('selecting dark mode applies data-theme="dark" to html element', () => {
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByText('Dark Mode'))
    fireEvent.click(screen.getByRole('button', { name: /continuar con dark mode/i }))
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  test('selecting original theme removes data-theme attribute', () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByText('Original'))
    fireEvent.click(screen.getByRole('button', { name: /continuar con original/i }))
    expect(document.documentElement.getAttribute('data-theme')).toBeNull()
  })

  test('selecting light mode saves nova_theme=light to localStorage', () => {
    renderWithTheme(<ThemePickerModal />)
    fireEvent.click(screen.getByText('Light Mode'))
    fireEvent.click(screen.getByRole('button', { name: /continuar con light mode/i }))
    expect(mockSetItem).toHaveBeenCalledWith('nova_theme', 'light')
  })
})

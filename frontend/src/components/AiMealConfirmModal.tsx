import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { ConfirmMealsRequest, FoodParseLogResponse } from '../services/api'

interface EditableItem {
  meal_type: string
  meal_label: string
  food_name: string
  display_name: string
  quantity_grams: number
  calories_per_100g: number
  carbs_per_100g: number
  protein_per_100g: number
  fat_per_100g: number
}

interface AiMealConfirmModalProps {
  isOpen: boolean
  previewData: FoodParseLogResponse | null
  onClose: () => void
  onConfirm: (request: ConfirmMealsRequest) => Promise<void>
  isSubmitting: boolean
  translateFoodName: (name: string) => string
}

const calcCalories = (item: EditableItem): number =>
  Math.round((item.calories_per_100g / 100) * item.quantity_grams)

const AiMealConfirmModal: React.FC<AiMealConfirmModalProps> = ({
  isOpen,
  previewData,
  onClose,
  onConfirm,
  isSubmitting,
  translateFoodName,
}) => {
  const [editedItems, setEditedItems] = useState<EditableItem[]>([])

  useEffect(() => {
    if (!previewData) return
    const items: EditableItem[] = []
    for (const meal of previewData.meals) {
      for (const item of meal.items) {
        items.push({
          meal_type: meal.meal_type,
          meal_label: meal.meal_label,
          food_name: item.food,
          display_name: translateFoodName(item.food),
          quantity_grams: item.quantity_grams,
          calories_per_100g: item.calories_per_100g,
          carbs_per_100g: item.carbs_per_100g,
          protein_per_100g: item.protein_per_100g,
          fat_per_100g: item.fat_per_100g,
        })
      }
    }
    setEditedItems(items)
  }, [previewData, translateFoodName])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  const handleQuantityChange = (index: number, rawValue: string) => {
    const parsed = parseFloat(rawValue)
    if (isNaN(parsed) || parsed < 0) return
    setEditedItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, quantity_grams: parsed } : item))
    )
  }

  const dayTotalCalories = editedItems.reduce((acc, item) => acc + calcCalories(item), 0)

  const handleConfirm = async () => {
    const validItems = editedItems.filter((item) => item.quantity_grams > 0)
    if (validItems.length === 0) return
    await onConfirm({
      items: validItems.map((item) => ({
        meal_type: item.meal_type,
        meal_label: item.meal_label,
        food_name: item.food_name,
        quantity_grams: item.quantity_grams,
        calories_per_100g: item.calories_per_100g,
        carbs_per_100g: item.carbs_per_100g,
        protein_per_100g: item.protein_per_100g,
        fat_per_100g: item.fat_per_100g,
      })),
    })
  }

  const mealGroups: { label: string; items: { item: EditableItem; index: number }[] }[] = []
  editedItems.forEach((item, index) => {
    const existing = mealGroups.find((g) => g.label === item.meal_label)
    if (existing) {
      existing.items.push({ item, index })
    } else {
      mealGroups.push({ label: item.meal_label, items: [{ item, index }] })
    }
  })

  if (!isOpen) return null

  return createPortal(
    <div className="ai-confirm-overlay" onClick={onClose}>
      <div
        className="ai-confirm-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-confirm-title"
      >
        <div className="ai-confirm-header">
          <h3 id="ai-confirm-title" className="ai-confirm-title">
            Revisá tu comida antes de guardar
          </h3>
          <button
            type="button"
            className="ai-confirm-close-btn"
            onClick={onClose}
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        <div className="ai-confirm-body">
          <div className="ai-confirm-modal">
            {mealGroups.length === 0 && (
              <p className="ai-confirm-empty">No hay items para confirmar.</p>
            )}

            {mealGroups.map((group) => {
              const groupCalories = group.items.reduce(
                (acc, { item }) => acc + calcCalories(item),
                0
              )

              return (
                <div key={group.label} className="ai-confirm-meal-group">
                  <h4 className="ai-confirm-meal-label">{group.label}</h4>
                  <div className="ai-confirm-table-wrapper">
                    <table className="ai-confirm-table">
                      <thead>
                        <tr>
                          <th className="ai-confirm-th ai-confirm-th--food">Alimento</th>
                          <th className="ai-confirm-th ai-confirm-th--qty">Cantidad (g)</th>
                          <th className="ai-confirm-th ai-confirm-th--cal">Cal</th>
                        </tr>
                      </thead>
                      <tbody>
                        {group.items.map(({ item, index }) => (
                          <tr key={index} className="ai-confirm-tr">
                            <td className="ai-confirm-td ai-confirm-td--food">
                              {item.display_name}
                            </td>
                            <td className="ai-confirm-td ai-confirm-td--qty">
                              <input
                                type="number"
                                min="1"
                                step="1"
                                className="ai-confirm-qty-input"
                                value={item.quantity_grams}
                                onChange={(e) => handleQuantityChange(index, e.target.value)}
                              />
                            </td>
                            <td className="ai-confirm-td ai-confirm-td--cal">
                              {calcCalories(item)}
                            </td>
                          </tr>
                        ))}
                        <tr className="ai-confirm-tr ai-confirm-tr--subtotal">
                          <td className="ai-confirm-td ai-confirm-td--food ai-confirm-subtotal-label">
                            Subtotal {group.label}
                          </td>
                          <td className="ai-confirm-td" />
                          <td className="ai-confirm-td ai-confirm-td--cal">
                            {Math.round(groupCalories)}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            })}

            {mealGroups.length > 1 && (
              <div className="ai-confirm-day-total">
                <span className="ai-confirm-day-total-label">Total del registro</span>
                <span className="ai-confirm-day-total-value">
                  {Math.round(dayTotalCalories)} kcal
                </span>
              </div>
            )}

            <div className="ai-confirm-actions">
              <button
                type="button"
                className="nutrition-secondary-button"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="nutrition-primary-button"
                onClick={handleConfirm}
                disabled={
                  isSubmitting ||
                  editedItems.filter((i) => i.quantity_grams > 0).length === 0
                }
              >
                {isSubmitting ? 'Guardando...' : 'Confirmar y guardar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}

export default AiMealConfirmModal

import React from 'react'
import { Sparkles } from 'lucide-react'

interface SuggestionData {
  suggestion: string
  type: string
  priority: string
  created_at: string
}

interface SuggestionCardProps {
  suggestion: SuggestionData | null
  className?: string
  loading?: boolean
}

const SuggestionCard: React.FC<SuggestionCardProps> = ({ 
  suggestion, 
  className = '',
  loading = false
}) => {
  return (
    <div className={`suggestion-card ${className}`}>
      {/* Header with AI badge */}
      <div className="suggestion-header">
        <div className="suggestion-title">
          <Sparkles className="suggestion-star" size={20} />
          <span>Suggestion of the Day</span>
        </div>
        <div className="suggestion-ai-badge">
          <Sparkles size={14} />
          <span>AI</span>
        </div>
      </div>

      {/* Content */}
      <div className="suggestion-content">
        {loading ? (
          <div className="suggestion-loading">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>Generating personalized suggestion...</p>
          </div>
        ) : (
          <p className="suggestion-text">
            {suggestion?.suggestion || 
             "Try doing a HIIT workout today to boost your calorie burn and improve your cardiovascular fitness."
            }
          </p>
        )}
      </div>
    </div>
  )
}

export default SuggestionCard
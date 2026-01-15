import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './AgeRestrictionModal.css'

function AgeRestrictionModal({ onConfirm, onDontShowAgain }) {
  const navigate = useNavigate()
  const [dontShowAgain, setDontShowAgain] = useState(false)

  const handleConfirm = () => {
    if (dontShowAgain && onDontShowAgain) {
      onDontShowAgain()
    }
    if (onConfirm) {
      onConfirm()
    }
  }

  return (
    <div className="age-restriction-overlay">
      <div className="age-restriction-modal">
        <button
          onClick={() => navigate('/')}
          className="age-restriction-back-button"
          aria-label="Вернуться на главную"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          <span>Назад</span>
        </button>
        <div className="age-restriction-content">
          <div className="age-restriction-icon">
            <svg 
              width="64" 
              height="64" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h2 className="age-restriction-title">Ой! Тут 18+</h2>
          <p className="age-restriction-message">
            Это аниме может содержать взрослый контент. Мы должны убедиться, что вам уже исполнилось 18 лет.
            <span className="age-restriction-divider"></span>
            <span className="age-restriction-legal-text">
              По требованию закона (ФЗ‑436) подтвердите, что вам есть 18 лет
            </span>
          </p>
          <div className="age-restriction-actions">
            <label className="age-restriction-checkbox-label">
              <input
                type="checkbox"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="age-restriction-checkbox"
              />
              <span className="age-restriction-checkbox-text">
                Больше не показывать это предупреждение
              </span>
            </label>
            <button
              onClick={handleConfirm}
              className="age-restriction-button"
            >
              Мне больше 18 лет
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AgeRestrictionModal

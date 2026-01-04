import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { userAPI } from '../services/api'
import './VerifyEmailPage.css'

function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('loading') // loading, success, error
  const [message, setMessage] = useState('')
  const token = searchParams.get('token')

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error')
        setMessage('Токен подтверждения не найден в ссылке')
        return
      }

      try {
        const response = await userAPI.verifyEmail(token)
        setStatus('success')
        setMessage(response.message || 'Email успешно подтвержден!')
        
        // Перезагружаем страницу, чтобы Layout загрузил пользователя с cookie
        // Перенаправляем на главную через 2 секунды, затем перезагружаем
        setTimeout(() => {
          window.location.href = '/'
        }, 2000)
      } catch (error) {
        setStatus('error')
        setMessage(error.response?.data?.detail || 'Ошибка при подтверждении email')
      }
    }

    verifyEmail()
  }, [token, navigate])

  return (
    <div className="verify-email-page">
      <div className="verify-email-container">
        {status === 'loading' && (
          <>
            <div className="verify-email-loading">
              <div className="spinner"></div>
              <h2>Подтверждение email...</h2>
              <p>Пожалуйста, подождите</p>
            </div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="verify-email-success">
              <div className="success-icon">✓</div>
              <h2>Email подтвержден!</h2>
              <p>{message}</p>
              <p className="redirect-message">Вы будете перенаправлены на главную страницу через несколько секунд...</p>
              <button 
                className="go-home-btn"
                onClick={() => window.location.href = '/'}
              >
                Перейти на главную
              </button>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="verify-email-error">
              <div className="error-icon">✕</div>
              <h2>Ошибка подтверждения</h2>
              <p>{message}</p>
              <button 
                className="go-home-btn"
                onClick={() => window.location.href = '/'}
              >
                Перейти на главную
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default VerifyEmailPage


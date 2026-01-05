import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import './SettingsPage.css'

function SettingsPage() {
  const { username } = useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        
        // Загружаем текущего пользователя
        try {
          const currentUserResponse = await userAPI.getCurrentUser()
          if (currentUserResponse.message) {
            setCurrentUser(currentUserResponse.message)
          }
        } catch (err) {
          console.log('Не авторизован')
        }

        // Загружаем данные пользователя для настроек
        const response = await userAPI.getUserSettings(username)
        if (response.message) {
          setUser(response.message)
        }
      } catch (err) {
        console.error('Ошибка загрузки настроек:', err)
        setError(err.response?.data?.detail || 'Ошибка загрузки настроек')
      } finally {
        setLoading(false)
      }
    }

    if (username) {
      loadData()
    }
  }, [username])

  // Проверяем, является ли текущий пользователь владельцем настроек
  const isOwner = currentUser && user && currentUser.username === user.username

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-container">
          <div className="loading-screen">
            <div className="loading-cat">
              <span className="cat-emoji">🐱</span>
            </div>
            <div className="loading-text">Загрузка...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="settings-page">
        <div className="settings-container">
          <div className="error-message">
            <p>{error}</p>
            <button onClick={() => navigate(-1)} className="back-button">
              Назад
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="settings-page">
        <div className="settings-container">
          <div className="error-message">
            <p>Пользователь не найден</p>
            <button onClick={() => navigate(-1)} className="back-button">
              Назад
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!isOwner) {
    return (
      <div className="settings-page">
        <div className="settings-container">
          <div className="error-message">
            <p>У вас нет доступа к настройкам этого пользователя</p>
            <button onClick={() => navigate(-1)} className="back-button">
              Назад
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <h1>Настройки</h1>
          <button onClick={() => navigate(`/profile/${username}`)} className="back-to-profile-button">
            ← Вернуться к профилю
          </button>
        </div>

        <div className="settings-content">
          <div className="settings-section">
            <h2>Информация о пользователе</h2>
            <div className="settings-info">
              <div className="info-item">
                <span className="info-label">Имя пользователя:</span>
                <span className="info-value">{user.username}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Email:</span>
                <span className="info-value">{user.email}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Роль:</span>
                <span className="info-value">{user.role}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Тип аккаунта:</span>
                <span className="info-value">{user.type_account}</span>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <h2>Дополнительные настройки</h2>
            <p className="settings-note">
              Здесь будут доступны дополнительные настройки аккаунта.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage


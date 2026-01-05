import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import CrownIcon from '../components/CrownIcon'
import './SettingsPage.css'

function SettingsPage() {
  const { username } = useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [avatarError, setAvatarError] = useState(false)

  useEffect(() => {
    setAvatarError(false)
    loadUserSettings()
    loadCurrentUser()
  }, [username])

  const loadCurrentUser = async () => {
    try {
      const response = await userAPI.getCurrentUser()
      if (response && response.message) {
        setCurrentUser({
          username: response.message.username,
          id: response.message.id
        })
      } else {
        setCurrentUser(null)
      }
    } catch (err) {
      setCurrentUser(null)
    }
  }

  const loadUserSettings = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await userAPI.getUserSettings(username)
      if (response && response.message) {
        setUser(response.message)
      } else {
        setError('Пользователь не найден')
      }
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err)
      setError('Ошибка при загрузке настроек')
    } finally {
      setLoading(false)
    }
  }

  // Проверяем, является ли текущий пользователь владельцем настроек
  const isOwner = currentUser && user && currentUser.username === user.username

  if (loading) {
    return (
      <div className="settings-page">
        <div className="container">
          <div className="loading-container">
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
        <div className="container">
          <div className="error-container">
            <h2>Ошибка</h2>
            <p>{error}</p>
            <button onClick={() => navigate('/')} className="back-btn">
              Вернуться на главную
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="settings-page">
        <div className="container">
          <div className="error-container">
            <h2>Пользователь не найден</h2>
            <button onClick={() => navigate('/')} className="back-btn">
              Вернуться на главную
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!isOwner) {
    return (
      <div className="settings-page">
        <div className="container">
          <div className="error-container">
            <h2>Доступ запрещен</h2>
            <p>Вы можете просматривать только свои настройки</p>
            <button onClick={() => navigate('/')} className="back-btn">
              Вернуться на главную
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="container">
        <div className="settings-header">
          <button 
            onClick={() => navigate(`/profile/${username}`)}
            className="back-to-profile-btn"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            <span>Назад к профилю</span>
          </button>
          <h1 className="settings-title">Настройки</h1>
        </div>

        <div className="settings-content">
          <div className="settings-section">
            <div className="settings-user-info">
              <div 
                className="settings-avatar"
                style={{
                  borderColor: '#ff0000',
                  boxShadow: '0 2px 8px #ff000040'
                }}
              >
                {(() => {
                  const avatarUrl = normalizeAvatarUrl(user.avatar_url)
                  if (avatarUrl && !avatarError) {
                    return (
                      <img 
                        src={avatarUrl} 
                        alt={user.username}
                        onError={() => setAvatarError(true)}
                        onLoad={() => setAvatarError(false)}
                      />
                    )
                  }
                  return (
                    <div className="avatar-fallback" style={{ backgroundColor: '#000000' }}>
                      <span style={{ fontSize: '2rem', lineHeight: '1' }}>🐱</span>
                    </div>
                  )
                })()}
              </div>
              <div className="settings-user-details">
                <h2 className="settings-username">
                  {user.username}
                  {user.id < 100 && (
                    <span className="crown-icon-small">
                      <CrownIcon size={16} />
                    </span>
                  )}
                </h2>
                <p className="settings-email">{user.email}</p>
                <p className="settings-role">Роль: {user.role}</p>
                <p className="settings-account-type">Тип аккаунта: {user.type_account}</p>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <h3 className="settings-section-title">Настройки аккаунта</h3>
            <div className="settings-actions">
              <p className="settings-info">
                Здесь будут доступны настройки вашего аккаунта.
              </p>
              <p className="settings-info">
                Для изменения имени пользователя и пароля используйте соответствующие функции в профиле.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage


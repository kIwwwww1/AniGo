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
  const [showChangeUsernameModal, setShowChangeUsernameModal] = useState(false)
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [usernameLoading, setUsernameLoading] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)

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

  const handleChangeUsername = async (e) => {
    e.preventDefault()
    setUsernameError('')
    
    if (!newUsername || newUsername.trim().length < 3 || newUsername.trim().length > 15) {
      setUsernameError('Имя пользователя должно быть от 3 до 15 символов')
      return
    }

    if (newUsername.trim() === user.username) {
      setUsernameError('Новое имя должно отличаться от текущего')
      return
    }

    try {
      setUsernameLoading(true)
      await userAPI.changeUsername(newUsername.trim())
      setShowChangeUsernameModal(false)
      setNewUsername('')
      // Обновляем данные пользователя
      await loadUserSettings()
      await loadCurrentUser()
      // Перенаправляем на новый username
      navigate(`/settings/${newUsername.trim()}`)
    } catch (err) {
      setUsernameError(err.response?.data?.detail || 'Ошибка при изменении имени')
    } finally {
      setUsernameLoading(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPasswordError('')
    
    if (!passwordForm.oldPassword || passwordForm.oldPassword.length < 8) {
      setPasswordError('Текущий пароль должен быть не менее 8 символов')
      return
    }

    if (!passwordForm.newPassword || passwordForm.newPassword.length < 8) {
      setPasswordError('Новый пароль должен быть не менее 8 символов')
      return
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('Новые пароли не совпадают')
      return
    }

    if (passwordForm.oldPassword === passwordForm.newPassword) {
      setPasswordError('Новый пароль должен отличаться от текущего')
      return
    }

    try {
      setPasswordLoading(true)
      await userAPI.changePassword(
        passwordForm.oldPassword,
        passwordForm.newPassword,
        passwordForm.confirmPassword
      )
      setShowChangePasswordModal(false)
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' })
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Ошибка при изменении пароля')
    } finally {
      setPasswordLoading(false)
    }
  }

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
                  <button 
                    className="edit-icon-btn"
                    onClick={() => {
                      setNewUsername(user.username)
                      setShowChangeUsernameModal(true)
                    }}
                    title="Изменить имя пользователя"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                </h2>
                <p className="settings-email">{user.email}</p>
                <p className="settings-password">
                  Пароль: <span className="password-masked">засекречено</span>
                  <button 
                    className="edit-icon-btn"
                    onClick={() => {
                      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' })
                      setShowChangePasswordModal(true)
                    }}
                    title="Изменить пароль"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                </p>
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

      {/* Модальное окно изменения имени */}
      {showChangeUsernameModal && (
        <div className="modal-overlay" onClick={() => setShowChangeUsernameModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close-btn"
              onClick={() => setShowChangeUsernameModal(false)}
              aria-label="Закрыть"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="modal-title">Изменить имя пользователя</h2>
            <form onSubmit={handleChangeUsername} className="register-form">
              <div className="form-group">
                <label htmlFor="new-username">Новое имя пользователя</label>
                <input
                  type="text"
                  id="new-username"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="От 3 до 15 символов"
                  minLength={3}
                  maxLength={15}
                  required
                  autoFocus
                />
              </div>
              {usernameError && (
                <div className="form-error">{usernameError}</div>
              )}
              <button 
                type="submit" 
                className="register-submit-btn"
                disabled={usernameLoading}
              >
                {usernameLoading ? 'Изменение...' : 'Изменить'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно изменения пароля */}
      {showChangePasswordModal && (
        <div className="modal-overlay" onClick={() => setShowChangePasswordModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close-btn"
              onClick={() => setShowChangePasswordModal(false)}
              aria-label="Закрыть"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="modal-title">Изменить пароль</h2>
            <form onSubmit={handleChangePassword} className="register-form">
              <div className="form-group">
                <label htmlFor="old-password">Текущий пароль</label>
                <input
                  type="password"
                  id="old-password"
                  value={passwordForm.oldPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, oldPassword: e.target.value})}
                  placeholder="Введите текущий пароль"
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label htmlFor="new-password">Новый пароль</label>
                <input
                  type="password"
                  id="new-password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})}
                  placeholder="Введите новый пароль (мин. 8 символов)"
                  minLength={8}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="confirm-password">Подтвердите новый пароль</label>
                <input
                  type="password"
                  id="confirm-password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
                  placeholder="Повторите новый пароль"
                  minLength={8}
                  required
                />
              </div>
              {passwordError && (
                <div className="form-error">{passwordError}</div>
              )}
              <button 
                type="submit" 
                className="register-submit-btn"
                disabled={passwordLoading}
              >
                {passwordLoading ? 'Изменение...' : 'Изменить пароль'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default SettingsPage


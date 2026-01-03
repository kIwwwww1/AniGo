import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { userAPI } from '../services/api'
import AnimeGrid from '../components/AnimeGrid'
import '../components/AnimeCardGrid.css'
import './UserProfilePage.css'
import '../pages/HomePage.css'

const AVAILABLE_COLORS = [
  { name: 'Белый', value: '#ffffff' },
  { name: 'Черный', value: '#000000' },
  { name: 'Серый', value: '#808080' },
  { name: 'Бежевый', value: '#c4c4af' },
  { name: 'Синий', value: '#0066ff' },
  { name: 'Зеленый', value: '#00cc00' },
  { name: 'Красный', value: '#ff0000' },
  { name: 'Розовый', value: '#ff69b4' },
  { name: 'Желтый', value: '#ffd700' },
  { name: 'Фиолетовый', value: '#9932cc' }
]

function UserProfilePage() {
  const { username } = useParams()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [usernameColor, setUsernameColor] = useState('#ffffff')
  const [avatarBorderColor, setAvatarBorderColor] = useState('#ff0000')
  const itemsPerPage = 6
  const maxPagesToShow = 3

  useEffect(() => {
    loadUserProfile()
    loadUserColors()
  }, [username])

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showSettings && !event.target.closest('.profile-settings-panel') && !event.target.closest('.profile-settings-icon')) {
        setShowSettings(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showSettings])

  const loadUserColors = () => {
    if (username) {
      const savedUsernameColor = localStorage.getItem(`user_${username}_username_color`)
      const savedAvatarBorderColor = localStorage.getItem(`user_${username}_avatar_border_color`)
      
      const availableColorValues = AVAILABLE_COLORS.map(c => c.value)
      
      if (savedUsernameColor && availableColorValues.includes(savedUsernameColor)) {
        setUsernameColor(savedUsernameColor)
      }
      if (savedAvatarBorderColor && availableColorValues.includes(savedAvatarBorderColor)) {
        setAvatarBorderColor(savedAvatarBorderColor)
      }
    }
  }

  const saveUsernameColor = (color) => {
    setUsernameColor(color)
    if (username) {
      localStorage.setItem(`user_${username}_username_color`, color)
    }
  }

  const saveAvatarBorderColor = (color) => {
    setAvatarBorderColor(color)
    if (username) {
      localStorage.setItem(`user_${username}_avatar_border_color`, color)
      // Обновляем глобальный цвет кнопок, если это профиль текущего пользователя
      updateGlobalAccentColorIfCurrentUser(color)
    }
  }

  const updateGlobalAccentColorIfCurrentUser = async (color) => {
    try {
      const response = await userAPI.getCurrentUser()
      if (response.message && response.message.username === username) {
        // Обновляем глобальный цвет
        document.documentElement.style.setProperty('--user-accent-color', color)
        
        // Создаем rgba версию для hover эффектов
        const hex = color.replace('#', '')
        const r = parseInt(hex.slice(0, 2), 16)
        const g = parseInt(hex.slice(2, 4), 16)
        const b = parseInt(hex.slice(4, 6), 16)
        const rgba = `rgba(${r}, ${g}, ${b}, 0.1)`
        document.documentElement.style.setProperty('--user-accent-color-rgba', rgba)
        
        // Создаем тень для text-shadow
        const shadowRgba = `rgba(${r}, ${g}, ${b}, 0.2)`
        document.documentElement.style.setProperty('--user-accent-color-shadow', shadowRgba)
        
        // Функции для создания вариаций цвета
        const lightenColor = (hex, percent) => {
          const num = parseInt(hex.replace('#', ''), 16)
          const r = Math.min(255, Math.floor((num >> 16) + (255 - (num >> 16)) * percent))
          const g = Math.min(255, Math.floor(((num >> 8) & 0x00FF) + (255 - ((num >> 8) & 0x00FF)) * percent))
          const b = Math.min(255, Math.floor((num & 0x0000FF) + (255 - (num & 0x0000FF)) * percent))
          return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
        }
        
        const darkenColor = (hex, percent) => {
          const num = parseInt(hex.replace('#', ''), 16)
          const r = Math.floor((num >> 16) * (1 - percent))
          const g = Math.floor(((num >> 8) & 0x00FF) * (1 - percent))
          const b = Math.floor((num & 0x0000FF) * (1 - percent))
          return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
        }
        
        // Функция для создания rgba
        const rgbaColor = (hex, alpha) => {
          const hexClean = hex.replace('#', '')
          const r = parseInt(hexClean.slice(0, 2), 16)
          const g = parseInt(hexClean.slice(2, 4), 16)
          const b = parseInt(hexClean.slice(4, 6), 16)
          return `rgba(${r}, ${g}, ${b}, ${alpha})`
        }
        
        // Создаем градиент для текста заголовков на основе выбранного цвета
        const lightColor = lightenColor(color, 0.4)
        const darkColor = darkenColor(color, 0.2)
        const gradientText = `linear-gradient(135deg, ${lightColor} 0%, ${color} 50%, ${darkColor} 100%)`
        document.documentElement.style.setProperty('--user-gradient-text', gradientText)
        
        // Создаем градиент для подчеркивания
        const gradientUnderline = `linear-gradient(90deg, ${lightColor} 0%, ${color} 100%)`
        document.documentElement.style.setProperty('--user-gradient-underline', gradientUnderline)
        
        // Создаем вариации цвета для оценок на карточках
        const lowColor = darkenColor(color, 0.3)
        const lowColorLight = lightenColor(lowColor, 0.2)
        document.documentElement.style.setProperty('--user-accent-color-low', lowColor)
        document.documentElement.style.setProperty('--user-accent-color-low-light', lowColorLight)
        document.documentElement.style.setProperty('--user-accent-color-border-low', rgbaColor(color, 0.4))
        document.documentElement.style.setProperty('--user-accent-color-shadow-low', rgbaColor(color, 0.3))
        
        const mediumColor = color
        const mediumColorLight = lightenColor(color, 0.15)
        document.documentElement.style.setProperty('--user-accent-color-medium', mediumColor)
        document.documentElement.style.setProperty('--user-accent-color-medium-light', mediumColorLight)
        document.documentElement.style.setProperty('--user-accent-color-border-medium', rgbaColor(color, 0.5))
        document.documentElement.style.setProperty('--user-accent-color-shadow-medium', rgbaColor(color, 0.4))
        
        const highColor = lightenColor(color, 0.2)
        const highColorLight = lightenColor(color, 0.35)
        document.documentElement.style.setProperty('--user-accent-color-high', highColor)
        document.documentElement.style.setProperty('--user-accent-color-high-light', highColorLight)
        document.documentElement.style.setProperty('--user-accent-color-border-high', rgbaColor(color, 0.6))
        document.documentElement.style.setProperty('--user-accent-color-shadow-high', rgbaColor(color, 0.5))
        
        const perfectColor = lightenColor(color, 0.4)
        document.documentElement.style.setProperty('--user-accent-color-perfect', perfectColor)
        document.documentElement.style.setProperty('--user-accent-color-shadow-perfect', rgbaColor(color, 0.6))
        document.documentElement.style.setProperty('--user-accent-color-shadow-perfect-light', rgbaColor(color, 0.3))
        
        document.documentElement.style.setProperty('--user-accent-color-border', rgbaColor(color, 0.3))
        
        // Создаем темный фон для идеальной оценки используя уже объявленные r, g, b
        const bgDark = `rgba(${Math.floor(r * 0.08)}, ${Math.floor(g * 0.08)}, ${Math.floor(b * 0.08)}, 0.95)`
        document.documentElement.style.setProperty('--user-accent-color-bg-dark', bgDark)
        
        // Отправляем событие для обновления в других компонентах
        window.dispatchEvent(new Event('userAccentColorUpdated'))
      }
    } catch (err) {
      // Игнорируем ошибки, если пользователь не авторизован
    }
  }

  const loadUserProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await userAPI.getUserProfile(username)
      if (response.message) {
        setUser(response.message)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Пользователь не найден')
      console.error('Ошибка загрузки профиля:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const hexToRgba = (hex, alpha = 0.3) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  const hexToRgb = (hex) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return { r, g, b }
  }

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="loading">Загрузка профиля...</div>
        </div>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="error-message">{error || 'Пользователь не найден'}</div>
        </div>
      </div>
    )
  }

  // Преобразуем избранное в формат аниме
  // favorites теперь уже массив объектов аниме, а не массив объектов с полем anime
  const favoritesAnime = user.favorites || []

  // Получаем статистику из ответа API
  const stats = user.stats || {
    favorites_count: favoritesAnime.length,
    ratings_count: 0,
    comments_count: 0,
    watch_history_count: 0,
    unique_watched_anime: 0
  }

  return (
    <div className="user-profile-page">
      <div className="container">
        <div className="profile-header">
          <div className="profile-settings-icon" onClick={() => setShowSettings(!showSettings)}>
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="1.5" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"></path>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </div>

          {showSettings && (
            <div className="profile-settings-panel">
              <div className="settings-panel-header">
                <h3>Настройки профиля</h3>
                <button className="settings-close-btn" onClick={() => setShowSettings(false)}>×</button>
              </div>
              <div className="settings-panel-content">
                <div className="color-picker-group">
                  <label>Цвет никнейма:</label>
                  <div className="color-buttons-grid">
                    {AVAILABLE_COLORS.map((color) => (
                      <button
                        key={color.value}
                        className={`color-button ${usernameColor === color.value ? 'active' : ''}`}
                        style={{ backgroundColor: color.value }}
                        onClick={() => saveUsernameColor(color.value)}
                        title={color.name}
                        aria-label={color.name}
                      >
                        {usernameColor === color.value && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="color-picker-group">
                  <label>Цвет обводки аватарки:</label>
                  <div className="color-buttons-grid">
                    {AVAILABLE_COLORS.map((color) => (
                      <button
                        key={color.value}
                        className={`color-button ${avatarBorderColor === color.value ? 'active' : ''}`}
                        style={{ backgroundColor: color.value }}
                        onClick={() => saveAvatarBorderColor(color.value)}
                        title={color.name}
                        aria-label={color.name}
                      >
                        {avatarBorderColor === color.value && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="profile-avatar-section">
            {user.avatar_url ? (
              <img 
                src={user.avatar_url} 
                alt={user.username}
                className="profile-avatar"
                style={{ 
                  borderColor: avatarBorderColor,
                  boxShadow: `0 8px 24px ${hexToRgba(avatarBorderColor, 0.3)}`
                }}
              />
            ) : (
              <div 
                className="profile-avatar" 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'var(--bg-secondary)',
                  color: 'var(--text-secondary)',
                  fontSize: '3rem',
                  fontWeight: 'bold',
                  borderColor: avatarBorderColor,
                  boxShadow: `0 8px 24px ${hexToRgba(avatarBorderColor, 0.3)}`
                }}
              >
                {user.username?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
          </div>
          <div className="profile-info-section">
            <h1 
              className="profile-username"
              style={{ 
                color: usernameColor
              }}
            >
              {user.username}
            </h1>
            {user.email && <p className="profile-email">{user.email}</p>}
            {user.created_at && (
              <p className="profile-joined">
                Присоединился: {formatDate(user.created_at)}
              </p>
            )}
            {user.role && (
              <span className={`profile-role role-${user.role}`}>
                {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
              </span>
            )}
          </div>
        </div>

        <div className="profile-stats">
          <div 
            className="stat-card" 
            style={{ 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={{ color: avatarBorderColor }}>{stats.favorites_count}</div>
            <div className="stat-label">Избранное</div>
          </div>
          <div 
            className="stat-card" 
            style={{ 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={{ color: avatarBorderColor }}>{stats.ratings_count}</div>
            <div className="stat-label">Оценок</div>
          </div>
          <div 
            className="stat-card" 
            style={{ 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={{ color: avatarBorderColor }}>{stats.comments_count}</div>
            <div className="stat-label">Комментариев</div>
          </div>
        </div>

        {favoritesAnime.length > 0 ? (
          <AnimeGrid
            title="Избранное"
            animeList={favoritesAnime}
            itemsPerPage={itemsPerPage}
            maxPagesToShow={maxPagesToShow}
            showExpandButton={false}
            showControls={favoritesAnime.length > itemsPerPage}
            showIndicators={favoritesAnime.length > itemsPerPage}
            emptyMessage="Нет избранных аниме"
            className="popular-anime-section"
          />
        ) : (
          <section className="popular-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Избранное</h2>
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              У пользователя нет избранных аниме
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default UserProfilePage

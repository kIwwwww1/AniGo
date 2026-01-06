import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import CrownIcon from '../components/CrownIcon'
import './SettingsPage.css'
import '../pages/UserProfilePage.css'

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

function SettingsPage() {
  const { username } = useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [avatarError, setAvatarError] = useState(false)
  const [usernameColor, setUsernameColor] = useState('#ffffff')
  const [avatarBorderColor, setAvatarBorderColor] = useState('#ff0000')
  const [themeColor1, setThemeColor1] = useState(null)
  const [themeColor2, setThemeColor2] = useState(null)
  const [gradientDirection, setGradientDirection] = useState('diagonal-right')
  const [isPremiumProfile, setIsPremiumProfile] = useState(false)
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
  const [badges, setBadges] = useState([])
  const [draggedBadge, setDraggedBadge] = useState(null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarHover, setAvatarHover] = useState(false)
  const [bestAnime, setBestAnime] = useState([])

  useEffect(() => {
    setAvatarError(false)
    loadUserSettings()
    loadCurrentUser()
    loadUserColors()
    loadThemeColor()
    loadBestAnime()
  }, [username])

  useEffect(() => {
    // Загружаем премиум профиль после загрузки user
    if (user) {
      loadPremiumProfile()
      loadBadges()
    }
  }, [user, username, bestAnime])

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getFavoritesBadge = (favoritesCount) => {
    if (favoritesCount >= 500) {
      return {
        id: 'favorites-500',
        level: 5,
        label: '500 избранных',
        className: 'favorites-badge-level-5',
        type: 'favorites'
      }
    } else if (favoritesCount >= 250) {
      return {
        id: 'favorites-250',
        level: 4,
        label: '250 избранных',
        className: 'favorites-badge-level-4',
        type: 'favorites'
      }
    } else if (favoritesCount >= 100) {
      return {
        id: 'favorites-100',
        level: 3,
        label: '100 избранных',
        className: 'favorites-badge-level-3',
        type: 'favorites'
      }
    } else if (favoritesCount >= 50) {
      return {
        id: 'favorites-50',
        level: 2,
        label: '50 избранных',
        className: 'favorites-badge-level-2',
        type: 'favorites'
      }
    } else if (favoritesCount >= 10) {
      return {
        id: 'favorites-10',
        level: 1,
        label: '10 избранных',
        className: 'favorites-badge-level-1',
        type: 'favorites'
      }
    }
    return null
  }

  const getAvailableBadges = () => {
    if (!user) return []
    
    const availableBadges = []
    
    // Бэдж роли (admin/owner/base/premium)
    if (user.type_account && (user.type_account === 'owner' || user.type_account === 'admin')) {
      availableBadges.push({
        id: 'role',
        type: 'role',
        label: user.type_account === 'admin' ? 'Администратор' : 'Владелец',
        className: `role-${user.type_account}`,
        defaultVisible: true
      })
    } else if (user.type_account && (user.type_account !== 'owner' && user.type_account !== 'admin')) {
      availableBadges.push({
        id: 'role',
        type: 'role',
        label: user.type_account === 'base' ? 'Базовый' : 
               user.type_account === 'premium' ? 'Премиум' : 
               user.type_account,
        className: `role-${user.type_account}`,
        defaultVisible: true
      })
    }
    
    // Бэдж "Один из 25"
    if (user.id < 25) {
      availableBadges.push({
        id: 'premium',
        type: 'premium',
        label: 'Один из 25',
        className: 'profile-premium-badge',
        defaultVisible: true
      })
    }
    
    // Бэдж даты регистрации
    if (user.created_at) {
      availableBadges.push({
        id: 'joined',
        type: 'joined',
        label: formatDate(user.created_at),
        className: 'profile-joined-badge',
        defaultVisible: true
      })
    }
    
    // Бэйдж за избранные аниме (показываем только самый высокий уровень)
    const favoritesCount = user.stats?.favorites_count || 0
    const favoritesBadge = getFavoritesBadge(favoritesCount)
    if (favoritesBadge) {
      availableBadges.push({
        ...favoritesBadge,
        defaultVisible: true
      })
    }
    
    // Бэйдж с топ-1 аниме пользователя
    const topAnime = bestAnime.find(anime => anime.place === 1)
    if (topAnime && topAnime.title) {
      availableBadges.push({
        id: 'top-anime',
        type: 'top-anime',
        label: topAnime.title,
        className: 'profile-top-anime-badge',
        defaultVisible: true
      })
    }
    
    return availableBadges
  }

  const loadBadges = () => {
    if (!user || !username) return
    
    const availableBadges = getAvailableBadges()
    const savedBadges = localStorage.getItem(`user_${username}_badges_config`)
    
    if (savedBadges) {
      try {
        const config = JSON.parse(savedBadges)
        
        // Удаляем старые бэйджи за избранные из конфигурации, если они есть
        const favoritesBadgeIds = ['favorites-10', 'favorites-50', 'favorites-100', 'favorites-250', 'favorites-500']
        const currentFavoritesBadge = availableBadges.find(b => b.type === 'favorites')
        
        // Очищаем старые бэйджи за избранные из порядка
        const cleanedOrder = config.order.filter(id => !favoritesBadgeIds.includes(id))
        const cleanedVisibility = { ...config.visibility }
        favoritesBadgeIds.forEach(id => {
          delete cleanedVisibility[id]
        })
        
        // Восстанавливаем порядок и видимость из сохраненных данных
        const orderedBadges = cleanedOrder
          .map(badgeId => {
            const badge = availableBadges.find(b => b.id === badgeId)
            if (badge) {
              return {
                ...badge,
                visible: cleanedVisibility[badgeId] !== undefined ? cleanedVisibility[badgeId] : badge.defaultVisible
              }
            }
            return null
          })
          .filter(Boolean)
        
        // Добавляем текущий бэйдж за избранные (если есть)
        if (currentFavoritesBadge) {
          const existingIndex = orderedBadges.findIndex(b => b.type === 'favorites')
          if (existingIndex >= 0) {
            // Заменяем старый бэйдж за избранные на новый
            orderedBadges[existingIndex] = {
              ...currentFavoritesBadge,
              visible: cleanedVisibility[currentFavoritesBadge.id] !== undefined ? cleanedVisibility[currentFavoritesBadge.id] : currentFavoritesBadge.defaultVisible
            }
          } else {
            // Добавляем новый бэйдж за избранные
            orderedBadges.push({
              ...currentFavoritesBadge,
              visible: cleanedVisibility[currentFavoritesBadge.id] !== undefined ? cleanedVisibility[currentFavoritesBadge.id] : currentFavoritesBadge.defaultVisible
            })
          }
        }
        
        // Добавляем другие новые бэйджи, которых нет в сохраненных
        availableBadges.forEach(badge => {
          if (badge.type !== 'favorites' && !orderedBadges.find(b => b.id === badge.id)) {
            orderedBadges.push({
              ...badge,
              visible: cleanedVisibility[badge.id] !== undefined ? cleanedVisibility[badge.id] : badge.defaultVisible
            })
          }
        })
        
        setBadges(orderedBadges)
        // Сохраняем обновленную конфигурацию
        saveBadgesConfig(orderedBadges)
      } catch (err) {
        console.error('Ошибка загрузки конфигурации бэджей:', err)
        setBadges(availableBadges)
      }
    } else {
      setBadges(availableBadges)
    }
  }

  const saveBadgesConfig = (badgesToSave) => {
    if (!username) return
    
    const config = {
      order: badgesToSave.map(b => b.id),
      visibility: {}
    }
    
    badgesToSave.forEach(badge => {
      config.visibility[badge.id] = badge.visible
    })
    
    localStorage.setItem(`user_${username}_badges_config`, JSON.stringify(config))
  }

  const handleBadgeDragStart = (e, index) => {
    setDraggedBadge(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleBadgeDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleBadgeDrop = (e, dropIndex) => {
    e.preventDefault()
    if (draggedBadge === null || draggedBadge === dropIndex) return
    
    const newBadges = [...badges]
    const draggedItem = newBadges[draggedBadge]
    newBadges.splice(draggedBadge, 1)
    newBadges.splice(dropIndex, 0, draggedItem)
    
    setBadges(newBadges)
    saveBadgesConfig(newBadges)
    setDraggedBadge(null)
  }

  const handleBadgeToggleVisibility = (badgeId) => {
    const newBadges = badges.map(badge => 
      badge.id === badgeId ? { ...badge, visible: !badge.visible } : badge
    )
    setBadges(newBadges)
    saveBadgesConfig(newBadges)
  }

  const handleAvatarFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Валидация типа файла
    if (!file.type.startsWith('image/')) {
      alert('Файл должен быть изображением')
      return
    }

    // Валидация размера файла (максимум 2 МБ)
    const MAX_FILE_SIZE = 2 * 1024 * 1024 // 2 МБ
    if (file.size > MAX_FILE_SIZE) {
      alert(`Размер файла не должен превышать 2 МБ. Текущий размер: ${(file.size / 1024 / 1024).toFixed(2)} МБ`)
      return
    }

    // Валидация размеров изображения
    const img = new Image()
    const objectUrl = URL.createObjectURL(file)
    
    img.onload = async () => {
      const MAX_DIMENSION = 2000 // Максимальный размер в пикселях
      if (img.width > MAX_DIMENSION || img.height > MAX_DIMENSION) {
        URL.revokeObjectURL(objectUrl)
        alert(`Размер изображения не должен превышать ${MAX_DIMENSION}x${MAX_DIMENSION} пикселей. Текущий размер: ${img.width}x${img.height}`)
        return
      }

      // Загружаем файл
      try {
        setAvatarUploading(true)
        const response = await userAPI.uploadAvatar(file)
        if (response && response.message) {
          // Обновляем аватар в состоянии пользователя
          setUser({ ...user, avatar_url: response.avatar_url || user.avatar_url })
          setAvatarError(false) // Сбрасываем ошибку аватара
          alert('Аватар успешно загружен')
        }
      } catch (err) {
        console.error('Ошибка загрузки аватара:', err)
        alert(err.response?.data?.detail || 'Ошибка при загрузке аватара')
      } finally {
        setAvatarUploading(false)
        URL.revokeObjectURL(objectUrl)
        // Сбрасываем input
        e.target.value = ''
      }
    }

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      alert('Ошибка при загрузке изображения')
      e.target.value = ''
    }

    img.src = objectUrl
  }

  // Слушаем изменения цветов и темы
  useEffect(() => {
    const handleColorUpdate = () => {
      loadUserColors()
    }
    
    const handleThemeUpdate = () => {
      loadThemeColor()
    }
    
    const handleStorageChange = (e) => {
      if (e.key && e.key.startsWith('user_') && e.key.endsWith('_username_color')) {
        loadUserColors()
      } else if (e.key && e.key.startsWith('user_') && e.key.endsWith('_avatar_border_color')) {
        loadUserColors()
      } else if (e.key === 'site-theme-color-1' || e.key === 'site-theme-color-2' || e.key === 'site-gradient-direction') {
        loadThemeColor()
      } else if (e.key && e.key.startsWith('user_') && e.key.endsWith('_premium_profile')) {
        if (user) {
          loadPremiumProfile()
        }
      }
    }
    
    window.addEventListener('avatarBorderColorUpdated', handleColorUpdate)
    window.addEventListener('userAccentColorUpdated', handleColorUpdate)
    window.addEventListener('siteThemeUpdated', handleThemeUpdate)
    window.addEventListener('storage', handleStorageChange)
    
    return () => {
      window.removeEventListener('avatarBorderColorUpdated', handleColorUpdate)
      window.removeEventListener('userAccentColorUpdated', handleColorUpdate)
      window.removeEventListener('siteThemeUpdated', handleThemeUpdate)
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [username, user])

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
      if (err.response?.status === 403) {
        setError('Ваш аккаунт заблокирован. Доступ к настройкам ограничен.')
      } else {
        setError('Ошибка при загрузке настроек')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadBestAnime = async () => {
    try {
      const response = await userAPI.getUserProfile(username)
      if (response && response.message && response.message.best_anime) {
        setBestAnime(response.message.best_anime || [])
      }
    } catch (err) {
      console.error('Ошибка загрузки топ-3 аниме:', err)
      setBestAnime([])
    }
  }

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

  const loadThemeColor = () => {
    const savedThemeColor1 = localStorage.getItem('site-theme-color-1')
    const savedThemeColor2 = localStorage.getItem('site-theme-color-2')
    const savedGradientDirection = localStorage.getItem('site-gradient-direction') || 'diagonal-right'
    
    if (savedThemeColor1 && AVAILABLE_COLORS.some(c => c.value === savedThemeColor1)) {
      setThemeColor1(savedThemeColor1)
      if (savedThemeColor2 && AVAILABLE_COLORS.some(c => c.value === savedThemeColor2)) {
        setThemeColor2(savedThemeColor2)
        setGradientDirection(savedGradientDirection)
        if (window.applyCustomTheme) {
          window.applyCustomTheme(savedThemeColor1, savedThemeColor2, savedGradientDirection)
        }
      } else {
        setThemeColor2(savedThemeColor1)
        setGradientDirection(savedGradientDirection)
        if (window.applyCustomTheme) {
          window.applyCustomTheme(savedThemeColor1, savedThemeColor1, savedGradientDirection)
        }
      }
    }
  }

  const hexToRgba = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  const createGradientFromColor = (color) => {
    // Функции для работы с цветом
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
    
    const lightColor = lightenColor(color, 0.3)
    const mediumColor = color
    const darkColor = darkenColor(color, 0.2)
    
    // Создаем градиент с вариациями цвета
    return `linear-gradient(135deg, ${darkColor} 0%, ${mediumColor} 25%, ${lightColor} 50%, ${mediumColor} 75%, ${darkColor} 100%)`
  }

  const getBadgeStyle = (badge) => {
    if (badge.type === 'top-anime') {
      const badgeGradient = createGradientFromColor(avatarBorderColor)
      const badgeShadow = hexToRgba(avatarBorderColor, 0.5)
      const badgeShadowLight = hexToRgba(avatarBorderColor, 0.3)
      const badgeTextShadow = hexToRgba(avatarBorderColor, 0.6)
      
      return {
        background: `linear-gradient(135deg, rgba(26, 26, 26, 0.8) 0%, rgba(20, 20, 20, 0.8) 100%) padding-box, ${badgeGradient} border-box`,
        borderColor: 'transparent',
        color: avatarBorderColor,
        boxShadow: `0 4px 16px ${badgeShadow}, 0 0 24px ${badgeShadowLight}, 0 0 40px ${badgeShadowLight}`,
        textShadow: `0 0 8px ${badgeTextShadow}, 0 0 16px ${badgeShadow}`
      }
    }
    return {}
  }

  const loadPremiumProfile = () => {
    if (username) {
      const savedPremium = localStorage.getItem(`user_${username}_premium_profile`)
      // Для пользователей с ID < 100 по умолчанию премиум включен, но можно отключить
      // Если в localStorage явно указано 'false', то отключаем
      if (savedPremium === 'false') {
        setIsPremiumProfile(false)
      } else if (savedPremium === 'true') {
        setIsPremiumProfile(true)
      } else {
        // Если нет сохраненного значения, для пользователей с ID < 100 включаем по умолчанию
        // Но только если user уже загружен
        if (user && user.id < 100) {
          setIsPremiumProfile(true)
        } else {
          setIsPremiumProfile(false)
        }
      }
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
      // Перезагружаем страницу после успешной смены имени
      window.location.reload()
    } catch (err) {
      setUsernameError(err.response?.data?.detail || 'Ошибка при изменении имени')
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
      // Удаляем сессию через API logout (удаляет куку на сервере)
      try {
        await userAPI.logout()
      } catch (logoutErr) {
        // Игнорируем ошибки logout, так как главное - пароль уже изменен
        console.log('Logout после смены пароля:', logoutErr)
      }
      // Перезагружаем страницу, чтобы пользователь зашел заново
      window.location.reload()
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Ошибка при изменении пароля')
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
          <div 
            className={`settings-section settings-user-section ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-header' : ''}`}
            style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? {} : {
              background: 'var(--theme-gradient, linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%))',
              borderColor: avatarBorderColor,
              boxShadow: `0 8px 48px ${hexToRgba(avatarBorderColor, 0.4)}, 0 0 0 1px ${avatarBorderColor}`
            }}
          >
            <div className="settings-user-info">
              <div 
                className={`settings-avatar ${avatarHover ? 'avatar-hover' : ''}`}
                style={{
                  borderColor: avatarBorderColor,
                  boxShadow: `0 2px 8px ${hexToRgba(avatarBorderColor, 0.4)}`
                }}
                onMouseEnter={() => setAvatarHover(true)}
                onMouseLeave={() => setAvatarHover(false)}
              >
                <input
                  type="file"
                  accept="image/*"
                  id="avatar-upload"
                  style={{ display: 'none' }}
                  onChange={handleAvatarFileSelect}
                  disabled={avatarUploading}
                />
                {(() => {
                  const avatarUrl = normalizeAvatarUrl(user.avatar_url)
                  if (avatarUrl && !avatarError) {
                    return (
                      <>
                        <img 
                          src={avatarUrl} 
                          alt={user.username}
                          onError={() => setAvatarError(true)}
                          onLoad={() => setAvatarError(false)}
                        />
                        {avatarHover && !avatarUploading && (
                          <div 
                            className="avatar-overlay"
                            onClick={() => document.getElementById('avatar-upload')?.click()}
                          >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                              <polyline points="17 8 12 3 7 8"></polyline>
                              <line x1="12" y1="3" x2="12" y2="15"></line>
                            </svg>
                            <span>Загрузить фото</span>
                          </div>
                        )}
                        {avatarUploading && (
                          <div className="avatar-uploading">
                            <div className="avatar-uploading-spinner"></div>
                            <span>Загрузка...</span>
                          </div>
                        )}
                      </>
                    )
                  }
                  return (
                    <>
                      <div className="avatar-fallback" style={{ backgroundColor: '#000000' }}>
                        <span style={{ fontSize: '2rem', lineHeight: '1' }}>🐱</span>
                      </div>
                      {avatarHover && !avatarUploading && (
                        <div 
                          className="avatar-overlay"
                          onClick={() => document.getElementById('avatar-upload')?.click()}
                        >
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                          </svg>
                          <span>Загрузить фото</span>
                        </div>
                      )}
                      {avatarUploading && (
                        <div className="avatar-uploading">
                          <div className="avatar-uploading-spinner"></div>
                          <span>Загрузка...</span>
                        </div>
                      )}
                    </>
                  )
                })()}
              </div>
              <div className="settings-user-details">
                <h2 
                  className={`settings-username ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-user' : ''}`}
                  style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
                    color: usernameColor
                  }}
                >
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
                <p className="settings-account-type">Тип аккаунта: {user.type_account}</p>
                
                {/* Управление бэйджами */}
                {badges.length > 0 && (
                  <div className="settings-badges-section">
                    <h3 className="settings-badges-title">Бэйджи профиля</h3>
                    <p className="settings-badges-description">
                      Перетаскивайте бэйджи для изменения порядка. Нажмите на глаз, чтобы скрыть/показать бэдж.
                    </p>
                    <div className="settings-badges-list">
                      {badges.map((badge, index) => (
                        <div
                          key={badge.id}
                          className={`settings-badge-item ${draggedBadge === index ? 'dragging' : ''}`}
                          draggable
                          onDragStart={(e) => handleBadgeDragStart(e, index)}
                          onDragOver={handleBadgeDragOver}
                          onDrop={(e) => handleBadgeDrop(e, index)}
                        >
                          <div className="badge-drag-handle">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="9" cy="12" r="1"></circle>
                              <circle cx="9" cy="5" r="1"></circle>
                              <circle cx="9" cy="19" r="1"></circle>
                              <circle cx="15" cy="12" r="1"></circle>
                              <circle cx="15" cy="5" r="1"></circle>
                              <circle cx="15" cy="19" r="1"></circle>
                            </svg>
                          </div>
                          <span 
                            className={`profile-role ${badge.className}`}
                            style={getBadgeStyle(badge)}
                          >
                            {badge.label}
                          </span>
                          <button
                            className={`badge-visibility-toggle ${badge.visible ? 'visible' : 'hidden'}`}
                            onClick={() => handleBadgeToggleVisibility(badge.id)}
                            title={badge.visible ? 'Скрыть бэдж' : 'Показать бэдж'}
                          >
                            {badge.visible ? (
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                              </svg>
                            ) : (
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                <line x1="1" y1="1" x2="23" y2="23"></line>
                              </svg>
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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


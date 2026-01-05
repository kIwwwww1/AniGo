import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import AnimeGrid from '../components/AnimeGrid'
import CrownIcon from '../components/CrownIcon'
import BestAnimeSection from '../components/BestAnimeSection'
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
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [usernameColor, setUsernameColor] = useState('#ffffff')
  const [avatarBorderColor, setAvatarBorderColor] = useState('#ff0000')
  const [themeColor1, setThemeColor1] = useState(null)
  const [themeColor2, setThemeColor2] = useState(null)
  const [gradientDirection, setGradientDirection] = useState('diagonal-right')
  const [avatarError, setAvatarError] = useState(false)
  const [isPremiumProfile, setIsPremiumProfile] = useState(false)
  const itemsPerPage = 6
  const maxPagesToShow = 3
  
  // Проверяем, является ли текущий пользователь владельцем профиля
  const isOwner = currentUser && user && currentUser.username === user.username
  
  const GRADIENT_DIRECTIONS = [
    { value: 'horizontal', label: '→', title: 'Горизонтально' },
    { value: 'vertical', label: '↓', title: 'Вертикально' },
    { value: 'diagonal-right', label: '↘', title: 'Диагональ вправо' },
    { value: 'diagonal-left', label: '↙', title: 'Диагональ влево' },
    { value: 'radial', label: '○', title: 'Радиальный' }
  ]

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
      // Пользователь не авторизован
      setCurrentUser(null)
    }
  }

  useEffect(() => {
    setAvatarError(false) // Сбрасываем ошибку при смене пользователя
    loadUserProfile()
    loadUserColors()
    loadThemeColor()
    loadCurrentUser()
  }, [username])

  useEffect(() => {
    // Загружаем премиум профиль после загрузки user
    if (user) {
      loadPremiumProfile()
    }
  }, [user, username])
  
  const loadThemeColor = () => {
    const savedThemeColor1 = localStorage.getItem('site-theme-color-1')
    const savedThemeColor2 = localStorage.getItem('site-theme-color-2')
    const savedGradientDirection = localStorage.getItem('site-gradient-direction') || 'diagonal-right'
    
    if (savedThemeColor1 && AVAILABLE_COLORS.some(c => c.value === savedThemeColor1)) {
      setThemeColor1(savedThemeColor1)
      if (savedThemeColor2 && AVAILABLE_COLORS.some(c => c.value === savedThemeColor2)) {
        setThemeColor2(savedThemeColor2)
        setGradientDirection(savedGradientDirection)
        applyCustomTheme(savedThemeColor1, savedThemeColor2, savedGradientDirection)
      } else {
        // Если есть только первый цвет, используем его для обоих
        setThemeColor2(savedThemeColor1)
        setGradientDirection(savedGradientDirection)
        applyCustomTheme(savedThemeColor1, savedThemeColor1, savedGradientDirection)
      }
    } else {
      setThemeColor1(null)
      setThemeColor2(null)
      setGradientDirection('diagonal-right')
      // Используем темную тему по умолчанию
      document.documentElement.setAttribute('data-theme', 'dark')
    }
  }
  
  // Делаем функцию доступной глобально для загрузки при старте
  const applyCustomTheme = (color1, color2, direction = 'diagonal-right') => {
    if (!color1 || !color2) return
    
    // Устанавливаем атрибут для кастомной темы
    document.documentElement.setAttribute('data-theme', 'custom')
    
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
    
    // Функция для создания rgba версии цвета
    const hexToRgba = (hex, alpha) => {
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
    
    // Функция для смешивания двух цветов
    const mixColors = (color1, color2, ratio) => {
      const hex1 = color1.replace('#', '')
      const hex2 = color2.replace('#', '')
      const r1 = parseInt(hex1.slice(0, 2), 16)
      const g1 = parseInt(hex1.slice(2, 4), 16)
      const b1 = parseInt(hex1.slice(4, 6), 16)
      const r2 = parseInt(hex2.slice(0, 2), 16)
      const g2 = parseInt(hex2.slice(2, 4), 16)
      const b2 = parseInt(hex2.slice(4, 6), 16)
      
      const r = Math.round(r1 + (r2 - r1) * ratio)
      const g = Math.round(g1 + (g2 - g1) * ratio)
      const b = Math.round(b1 + (b2 - b1) * ratio)
      
      return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
    }
    
    // Создаем градиенты только для плашек в профиле (не для основного фона сайта)
    // Используем более яркие и заметные цвета с прозрачностью для лучшей видимости
    const lightBg1 = lightenColor(color1, 0.3)
    const mediumBg1 = color1
    const darkBg1 = darkenColor(color1, 0.2)
    
    const lightBg2 = lightenColor(color2, 0.3)
    const mediumBg2 = color2
    const darkBg2 = darkenColor(color2, 0.2)
    
    // Создаем множество промежуточных цветов для максимально плавного перехода
    const mix1 = mixColors(color1, color2, 0.2)   // 20% смеси
    const mix2 = mixColors(color1, color2, 0.4)   // 40% смеси
    const mix3 = mixColors(color1, color2, 0.5)    // 50% смеси (середина)
    const mix4 = mixColors(color1, color2, 0.6)    // 60% смеси
    const mix5 = mixColors(color1, color2, 0.8)   // 80% смеси
    
    // Создаем rgba версии для смешивания с темным фоном
    const rgba1 = hexToRgba(color1, 0.4)
    const rgba2 = hexToRgba(color2, 0.4)
    const rgba1Light = hexToRgba(lightBg1, 0.3)
    const rgba2Light = hexToRgba(lightBg2, 0.3)
    
    // Промежуточные rgba цвета с плавным изменением прозрачности
    const rgbaMix1 = hexToRgba(mix1, 0.38)
    const rgbaMix2 = hexToRgba(mix2, 0.37)
    const rgbaMix3 = hexToRgba(mix3, 0.36)
    const rgbaMix4 = hexToRgba(mix4, 0.37)
    const rgbaMix5 = hexToRgba(mix5, 0.38)
    
    // Определяем направление градиента
    let gradientString = ''
    if (direction === 'radial') {
      gradientString = `radial-gradient(circle, ${rgba1Light} 0%, ${rgba1} 12%, ${rgbaMix1} 25%, ${rgbaMix2} 37%, ${rgbaMix3} 50%, ${rgbaMix4} 62%, ${rgbaMix5} 75%, ${rgba2} 88%, ${rgba2Light} 100%)`
    } else {
      let angle = '135deg' // diagonal-right по умолчанию
      if (direction === 'horizontal') angle = 'to right'
      else if (direction === 'vertical') angle = 'to bottom'
      else if (direction === 'diagonal-right') angle = '135deg'
      else if (direction === 'diagonal-left') angle = '45deg'
      
      // Максимально плавный градиент с множеством промежуточных точек и равномерным распределением
      gradientString = `linear-gradient(${angle}, ${rgba1Light} 0%, ${rgba1} 5%, ${rgbaMix1} 12%, ${rgbaMix2} 20%, ${rgbaMix3} 30%, ${rgbaMix4} 42%, ${rgbaMix5} 55%, ${rgba2} 68%, ${rgba2Light} 80%, ${rgba2} 90%, ${rgba2Light} 100%)`
    }
    
    // Обратный градиент для некоторых элементов
    let reverseGradientString = ''
    if (direction === 'radial') {
      reverseGradientString = `radial-gradient(circle, ${rgba2Light} 0%, ${rgba2} 12%, ${rgbaMix5} 25%, ${rgbaMix4} 37%, ${rgbaMix3} 50%, ${rgbaMix2} 62%, ${rgbaMix1} 75%, ${rgba1} 88%, ${rgba1Light} 100%)`
    } else {
      let angle = '135deg'
      if (direction === 'horizontal') angle = 'to left'
      else if (direction === 'vertical') angle = 'to top'
      else if (direction === 'diagonal-right') angle = '315deg'
      else if (direction === 'diagonal-left') angle = '225deg'
      
      // Максимально плавный градиент с множеством промежуточных точек и равномерным распределением
      reverseGradientString = `linear-gradient(${angle}, ${rgba2Light} 0%, ${rgba2} 5%, ${rgbaMix5} 12%, ${rgbaMix4} 20%, ${rgbaMix3} 30%, ${rgbaMix2} 42%, ${rgbaMix1} 55%, ${rgba1} 68%, ${rgba1Light} 80%, ${rgba1} 90%, ${rgba1Light} 100%)`
    }
    
    // Применяем только CSS переменные для градиентов плашек
    // НЕ меняем основной фон сайта (--bg-primary, --bg-secondary, --bg-card остаются по умолчанию)
    document.documentElement.style.setProperty('--theme-color', color1)
    document.documentElement.style.setProperty('--theme-gradient', gradientString)
    document.documentElement.style.setProperty('--theme-gradient-reverse', reverseGradientString)
  }
  
  // Делаем функцию глобальной
  window.applyCustomTheme = applyCustomTheme
  
  const handleThemeColor1Change = (color) => {
    // Не позволяем менять градиент при активном премиум профиле
    if ((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) {
      return
    }
    setThemeColor1(color)
    const color2 = themeColor2 || color
    setThemeColor2(color2)
    applyCustomTheme(color, color2, gradientDirection)
    localStorage.setItem('site-theme-color-1', color)
    if (!localStorage.getItem('site-theme-color-2')) {
      localStorage.setItem('site-theme-color-2', color2)
    }
    window.dispatchEvent(new Event('siteThemeUpdated'))
  }
  
  const handleThemeColor2Change = (color) => {
    // Не позволяем менять градиент при активном премиум профиле
    if ((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) {
      return
    }
    setThemeColor2(color)
    const color1 = themeColor1 || color
    setThemeColor1(color1)
    applyCustomTheme(color1, color, gradientDirection)
    localStorage.setItem('site-theme-color-2', color)
    if (!localStorage.getItem('site-theme-color-1')) {
      localStorage.setItem('site-theme-color-1', color1)
    }
    window.dispatchEvent(new Event('siteThemeUpdated'))
  }
  
  const handleGradientDirectionChange = (direction) => {
    // Не позволяем менять градиент при активном премиум профиле
    if ((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) {
      return
    }
    setGradientDirection(direction)
    if (themeColor1 && themeColor2) {
      applyCustomTheme(themeColor1, themeColor2, direction)
      localStorage.setItem('site-gradient-direction', direction)
      window.dispatchEvent(new Event('siteThemeUpdated'))
    }
  }
  
  const handleResetTheme = () => {
    // Не позволяем сбрасывать градиент при активном премиум профиле
    if ((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) {
      return
    }
    setThemeColor1(null)
    setThemeColor2(null)
    setGradientDirection('diagonal-right')
    localStorage.removeItem('site-theme-color-1')
    localStorage.removeItem('site-theme-color-2')
    localStorage.removeItem('site-gradient-direction')
    document.documentElement.setAttribute('data-theme', 'dark')
    // Сбрасываем только CSS переменные градиентов
    document.documentElement.style.removeProperty('--theme-color')
    document.documentElement.style.removeProperty('--theme-gradient')
    document.documentElement.style.removeProperty('--theme-gradient-reverse')
    window.dispatchEvent(new Event('siteThemeUpdated'))
  }

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

  const togglePremiumProfile = () => {
    const newPremiumState = !isPremiumProfile
    console.log('Toggle premium profile:', newPremiumState, 'Current state:', isPremiumProfile, 'username:', username)
    setIsPremiumProfile(newPremiumState)
    if (username) {
      localStorage.setItem(`user_${username}_premium_profile`, newPremiumState.toString())
      console.log('Saved to localStorage:', `user_${username}_premium_profile = ${newPremiumState}`)
    } else {
      console.warn('Cannot save premium profile: username is not available')
    }
  }

  const saveUsernameColor = (color) => {
    // Не позволяем менять цвет при активном премиум профиле
    if ((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) {
      return
    }
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
      // Отправляем событие для обновления цвета в Layout
      window.dispatchEvent(new Event('avatarBorderColorUpdated'))
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
      setAvatarError(false) // Сбрасываем ошибку аватарки при загрузке
      const response = await userAPI.getUserProfile(username)
      if (response.message) {
        console.log('User profile loaded:', response.message)
        console.log('Avatar URL from API:', response.message.avatar_url)
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

  const getFavoritesBadge = (favoritesCount) => {
    if (favoritesCount >= 500) {
      return {
        id: 'favorites-500',
        level: 5,
        label: '500 избранных',
        className: 'favorites-badge-level-5'
      }
    } else if (favoritesCount >= 250) {
      return {
        id: 'favorites-250',
        level: 4,
        label: '250 избранных',
        className: 'favorites-badge-level-4'
      }
    } else if (favoritesCount >= 100) {
      return {
        id: 'favorites-100',
        level: 3,
        label: '100 избранных',
        className: 'favorites-badge-level-3'
      }
    } else if (favoritesCount >= 50) {
      return {
        id: 'favorites-50',
        level: 2,
        label: '50 избранных',
        className: 'favorites-badge-level-2'
      }
    } else if (favoritesCount >= 10) {
      return {
        id: 'favorites-10',
        level: 1,
        label: '10 избранных',
        className: 'favorites-badge-level-1'
      }
    }
    return null
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

  // Получаем топ-3 аниме
  const bestAnime = user.best_anime || []

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
        <div 
          className={`profile-header ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-header' : ''}`}
          style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : {
            borderColor: avatarBorderColor,
            boxShadow: `0 8px 48px ${hexToRgba(avatarBorderColor, 0.4)}, 0 0 0 1px ${avatarBorderColor}`
          }}
        >
          {isOwner && (
            <>
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
                        disabled={((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile)}
                      >
                        {usernameColor === color.value && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                  {((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) && (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      Недоступно при активном премиум профиле
                    </p>
                  )}
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
                <div className="theme-color-group">
                  <label>Градиент темы сайта:</label>
                  <div className="theme-color-buttons">
                    <button
                      className={`theme-color-reset-btn ${themeColor1 === null ? 'active' : ''}`}
                      onClick={handleResetTheme}
                      title="Темная тема по умолчанию"
                      disabled={(user && user.id < 100) || isPremiumProfile}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                      </svg>
                      <span>По умолчанию</span>
                    </button>
                  </div>
                  <div className="theme-color-picker">
                    <label className="theme-color-label">Цвет 1:</label>
                    <div className="color-buttons-grid color-buttons-scrollable">
                      {AVAILABLE_COLORS.map((color) => (
                        <button
                          key={`color1-${color.value}`}
                          className={`color-button theme-color-button ${themeColor1 === color.value ? 'active' : ''}`}
                          style={{ backgroundColor: color.value }}
                          onClick={() => handleThemeColor1Change(color.value)}
                          title={color.name}
                          aria-label={color.name}
                          disabled={((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile)}
                        >
                          {themeColor1 === color.value && (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="theme-color-picker">
                    <label className="theme-color-label">Цвет 2:</label>
                    <div className="color-buttons-grid color-buttons-scrollable">
                      {AVAILABLE_COLORS.map((color) => (
                        <button
                          key={`color2-${color.value}`}
                          className={`color-button theme-color-button ${themeColor2 === color.value ? 'active' : ''}`}
                          style={{ backgroundColor: color.value }}
                          onClick={() => handleThemeColor2Change(color.value)}
                          title={color.name}
                          aria-label={color.name}
                          disabled={((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile)}
                        >
                          {themeColor2 === color.value && (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="gradient-direction-group">
                    <label className="gradient-direction-label">Направление градиента:</label>
                    <div className="gradient-direction-buttons">
                      {GRADIENT_DIRECTIONS.map((dir) => (
                        <button
                          key={dir.value}
                          className={`gradient-direction-btn ${gradientDirection === dir.value ? 'active' : ''}`}
                          onClick={() => handleGradientDirectionChange(dir.value)}
                          title={dir.title}
                          aria-label={dir.title}
                          disabled={((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile)}
                        >
                          {dir.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  {((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) && (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      Недоступно при активном премиум профиле
                    </p>
                  )}
                </div>
                <div className="premium-profile-group">
                  <label>Премиум оформление:</label>
                  <button
                    className={`premium-profile-toggle ${(user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'active' : ''}`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      console.log('Premium button clicked, current state:', isPremiumProfile, 'user:', user)
                      togglePremiumProfile()
                    }}
                    type="button"
                  >
                    <span className="premium-toggle-label">
                      {(user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? '✓ Премиум профиль активен' : 'Премиум профиль'}
                    </span>
                    {((user && user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) && (
                      <CrownIcon size={20} />
                    )}
                  </button>
                  <p className="premium-profile-description">
                    {user && user.id < 100 
                      ? 'Вы один из первых 100 пользователей - можете включать/отключать премиум оформление'
                      : 'Включает золотой градиент для имени пользователя и карточек аниме'
                    }
                  </p>
                </div>
              </div>
            </div>
              )}
            </>
          )}

          <div className="profile-avatar-section">
            {(() => {
              const avatarUrl = normalizeAvatarUrl(user.avatar_url)
              console.log('Avatar URL after normalization:', avatarUrl)
              console.log('Avatar error state:', avatarError)
              console.log('User avatar_url from API:', user.avatar_url)
              
              if (avatarUrl && !avatarError) {
                return (
                  <img 
                    src={avatarUrl} 
                    alt={user.username}
                    className={`profile-avatar ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-avatar' : ''}`}
                    style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
                      borderColor: avatarBorderColor,
                      boxShadow: `0 8px 24px ${hexToRgba(avatarBorderColor, 0.3)}`
                    }}
                    onError={(e) => {
                      console.error('Error loading avatar:', avatarUrl, e)
                      setAvatarError(true)
                    }}
                    onLoad={() => {
                      console.log('Avatar loaded successfully:', avatarUrl)
                      setAvatarError(false)
                    }}
                  />
                )
              } else {
                console.log('Showing fallback avatar (cat sticker). Reason:', {
                  avatarUrl,
                  avatarError,
                  userAvatarUrl: user.avatar_url
                })
                return (
                  <div 
                    className={`profile-avatar profile-avatar-fallback ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-avatar' : ''}`}
                    style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? {
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#000000'
                    } : {
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#000000',
                      borderColor: avatarBorderColor,
                      boxShadow: `0 8px 24px ${hexToRgba(avatarBorderColor, 0.3)}`
                    }}
                  >
                    <span style={{ fontSize: '5rem', lineHeight: '1' }}>🐱</span>
                  </div>
                )
              }
            })()}
          </div>
          <div className="profile-info-section">
            <h1 
              className={`profile-username ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-user' : ''}`}
              style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
                color: usernameColor
              }}
              data-premium={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile}
            >
              {user.username}
              {user.id < 100 && (
                <span className="crown-icon">
                  <CrownIcon size={28} />
                </span>
              )}
            </h1>
            <div className="profile-badges">
              {(() => {
                // Получаем конфигурацию бэджей из localStorage
                const savedBadges = localStorage.getItem(`user_${username}_badges_config`)
                let badgesConfig = null
                
                if (savedBadges) {
                  try {
                    badgesConfig = JSON.parse(savedBadges)
                  } catch (err) {
                    console.error('Ошибка загрузки конфигурации бэджей:', err)
                  }
                }
                
                // Создаем массив всех доступных бэджей
                const allBadges = []
                
                if (user.type_account && (user.type_account === 'owner' || user.type_account === 'admin')) {
                  allBadges.push({
                    id: 'role',
                    element: (
                      <span key="role" className={`profile-role role-${user.type_account}`}>
                        {user.type_account === 'admin' ? 'Администратор' : 'Владелец'}
                      </span>
                    )
                  })
                } else if (user.type_account && (user.type_account !== 'owner' && user.type_account !== 'admin')) {
                  allBadges.push({
                    id: 'role',
                    element: (
                      <span key="role" className={`profile-role role-${user.type_account}`}>
                        {user.type_account === 'base' ? 'Базовый' : 
                         user.type_account === 'premium' ? 'Премиум' : 
                         user.type_account}
                      </span>
                    )
                  })
                }
                
                if (user.id < 100) {
                  allBadges.push({
                    id: 'premium',
                    element: (
                      <span key="premium" className="profile-role profile-premium-badge">
                        Один из 100
                      </span>
                    )
                  })
                }
                
                if (user.created_at) {
                  allBadges.push({
                    id: 'joined',
                    element: (
                      <span key="joined" className="profile-role profile-joined-badge">
                        {formatDate(user.created_at)}
                      </span>
                    )
                  })
                }
                
                // Бэйдж за избранные аниме (показываем только самый высокий уровень)
                const favoritesCount = user.stats?.favorites_count || (user.favorites?.length || 0)
                const favoritesBadge = getFavoritesBadge(favoritesCount)
                if (favoritesBadge) {
                  allBadges.push({
                    id: favoritesBadge.id,
                    element: (
                      <span key={favoritesBadge.id} className={`profile-role ${favoritesBadge.className}`}>
                        {favoritesBadge.label}
                      </span>
                    )
                  })
                }
                
                // Если есть сохраненная конфигурация, используем её порядок и видимость
                if (badgesConfig) {
                  // Удаляем старые бэйджи за избранные из конфигурации
                  const favoritesBadgeIds = ['favorites-10', 'favorites-50', 'favorites-100', 'favorites-250', 'favorites-500']
                  const currentFavoritesBadge = allBadges.find(b => b.id && b.id.startsWith('favorites-'))
                  
                  // Очищаем старые бэйджи за избранные из порядка
                  const cleanedOrder = badgesConfig.order.filter(id => !favoritesBadgeIds.includes(id))
                  
                  const orderedBadges = cleanedOrder
                    .map(badgeId => {
                      const badge = allBadges.find(b => b.id === badgeId)
                      if (badge && badgesConfig.visibility[badgeId] !== false) {
                        return badge.element
                      }
                      return null
                    })
                    .filter(Boolean)
                  
                  // Добавляем текущий бэйдж за избранные (если есть и видим)
                  if (currentFavoritesBadge && badgesConfig.visibility[currentFavoritesBadge.id] !== false) {
                    const existingIndex = orderedBadges.findIndex((_, idx) => {
                      const badgeId = cleanedOrder[idx]
                      return badgeId && badgeId.startsWith('favorites-')
                    })
                    if (existingIndex >= 0) {
                      orderedBadges[existingIndex] = currentFavoritesBadge.element
                    } else {
                      orderedBadges.push(currentFavoritesBadge.element)
                    }
                  }
                  
                  // Добавляем другие новые бэйджи, которых нет в сохраненных
                  allBadges.forEach(badge => {
                    if (badge.id && !badge.id.startsWith('favorites-') && 
                        !badgesConfig.order.includes(badge.id) && 
                        badgesConfig.visibility[badge.id] !== false) {
                      orderedBadges.push(badge.element)
                    }
                  })
                  
                  return orderedBadges
                }
                
                // Если нет сохраненной конфигурации, показываем все бэйджи в порядке по умолчанию
                return allBadges.map(b => b.element)
              })()}
            </div>
          </div>
        </div>

        <div className={`profile-stats ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-stats' : ''}`}>
          <div 
            className="stat-card" 
            style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.favorites_count}</div>
            <div className={`stat-label ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-label' : ''}`}>Избранное</div>
          </div>
          <div 
            className="stat-card" 
            style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.ratings_count}</div>
            <div className={`stat-label ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-label' : ''}`}>Оценок</div>
          </div>
          <div 
            className="stat-card" 
            style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.comments_count}</div>
            <div className={`stat-label ${(user.id < 100 && isPremiumProfile !== false) || isPremiumProfile ? 'premium-label' : ''}`}>Комментариев</div>
          </div>
        </div>

        <BestAnimeSection
          bestAnime={bestAnime}
          favorites={favoritesAnime}
          isOwner={isOwner}
          onUpdate={loadUserProfile}
        />

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
            className={user && ((user.id < 100 && isPremiumProfile !== false) || isPremiumProfile) ? 'premium-anime-grid' : ''}
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

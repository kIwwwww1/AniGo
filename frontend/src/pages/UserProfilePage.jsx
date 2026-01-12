import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import { getFromCache, setToCache, removeFromCache, clearUserProfileCache } from '../utils/cache'
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
  const [isPremiumProfile, setIsPremiumProfile] = useState(false) // false по умолчанию, чтобы не мигать премиум темой
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
    
    // Обработчик удаления кэша - автоматическая перезагрузка данных
    const handleCacheRemoved = (event) => {
      const removedKey = event?.detail?.key
      const CACHE_KEY = `user_profile_${username}`
      
      // Проверяем, относится ли удаленный кэш к профилю пользователя
      if (removedKey === CACHE_KEY || removedKey?.includes(`user_profile_${username}`)) {
        loadUserProfile()
      }
    }
    
    window.addEventListener('cacheRemoved', handleCacheRemoved)
    
    // При уходе со страницы профиля восстанавливаем цвета текущего авторизованного пользователя
    return async () => {
      window.removeEventListener('cacheRemoved', handleCacheRemoved)
      // Сохраняем ссылку на функцию для использования в cleanup
      const applyFn = restoreCurrentUserColorsRef.current
      if (applyFn) {
        try {
          const response = await userAPI.getCurrentUser()
          if (response.message && response.message.username) {
            // Загружаем настройки профиля текущего пользователя из API
            const settingsResponse = await userAPI.getProfileSettings()
            if (settingsResponse.message && settingsResponse.message.avatar_border_color) {
              const savedColor = settingsResponse.message.avatar_border_color
              const availableColors = ['#ffffff', '#000000', '#808080', '#c4c4af', '#0066ff', '#00cc00', '#ff0000', '#ff69b4', '#ffd700', '#9932cc']
              
              if (availableColors.includes(savedColor)) {
                // Применяем цвета текущего пользователя
                applyFn(savedColor)
              } else {
                // Используем цвет по умолчанию
                applyFn('#ff0000')
              }
            } else {
              // Используем цвет по умолчанию
              applyFn('#ff0000')
            }
          } else {
            // Если пользователь не авторизован, используем дефолтные цвета
            applyFn('#e50914')
          }
        } catch (err) {
          // Если не удалось загрузить настройки, используем дефолтные цвета
          applyFn('#e50914')
        }
      }
    }
  }, [username])

  // Удаляем этот useEffect, так как премиум статус теперь загружается в loadUserProfile
  // useEffect(() => {
  //   // Загружаем премиум профиль после загрузки user
  //   if (user) {
  //     loadPremiumProfile()
  //   }
  // }, [user, username])
  
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
  
  const handleThemeColor1Change = async (color) => {
    // Не позволяем менять градиент при активном премиум профиле
    if (isPremiumProfile) {
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
    
    // Сохраняем в API, если это профиль текущего пользователя
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          theme_color_1: color,
          theme_color_2: color2,
          gradient_direction: gradientDirection
        })
      } catch (err) {
        console.error('Ошибка сохранения градиента:', err)
      }
    }
    
    window.dispatchEvent(new Event('siteThemeUpdated'))
  }
  
  const handleThemeColor2Change = async (color) => {
    // Не позволяем менять градиент при активном премиум профиле
    if (isPremiumProfile) {
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
    
    // Сохраняем в API, если это профиль текущего пользователя
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          theme_color_1: color1,
          theme_color_2: color,
          gradient_direction: gradientDirection
        })
      } catch (err) {
        console.error('Ошибка сохранения градиента:', err)
      }
    }
    
    window.dispatchEvent(new Event('siteThemeUpdated'))
  }
  
  const handleGradientDirectionChange = async (direction) => {
    // Не позволяем менять градиент при активном премиум профиле
    if (isPremiumProfile) {
      return
    }
    setGradientDirection(direction)
    if (themeColor1 && themeColor2) {
      applyCustomTheme(themeColor1, themeColor2, direction)
      localStorage.setItem('site-gradient-direction', direction)
      
      // Сохраняем в API, если это профиль текущего пользователя
      if (username && currentUser && currentUser.username === username) {
        try {
          await userAPI.updateProfileSettings({
            theme_color_1: themeColor1,
            theme_color_2: themeColor2,
            gradient_direction: direction
          })
          console.log('Направление градиента сохранено в API:', direction)
        } catch (err) {
          console.error('Ошибка сохранения направления градиента:', err)
        }
      }
      
      window.dispatchEvent(new Event('siteThemeUpdated'))
    }
  }
  
  const handleResetTheme = async () => {
    // Не позволяем сбрасывать градиент при активном премиум профиле
    if (isPremiumProfile) {
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
    
    // Сохраняем в API, если это профиль текущего пользователя
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          theme_color_1: null,
          theme_color_2: null,
          gradient_direction: 'diagonal-right'
        })
      } catch (err) {
        console.error('Ошибка сброса градиента:', err)
      }
    }
    
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

  // Ref для хранения ссылки на функцию применения цветов
  const restoreCurrentUserColorsRef = { current: null }

  // Функция для применения цвета обводки аватарки к темам аниме карточек
  const applyAvatarBorderColorToAnimeThemes = (color) => {
    // Сохраняем ссылку на функцию для использования в cleanup useEffect
    restoreCurrentUserColorsRef.current = applyAvatarBorderColorToAnimeThemes
    if (!color) return
    
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
    
    // Функция для создания rgba
    const rgbaColor = (hex, alpha) => {
      const hexClean = hex.replace('#', '')
      const r = parseInt(hexClean.slice(0, 2), 16)
      const g = parseInt(hexClean.slice(2, 4), 16)
      const b = parseInt(hexClean.slice(4, 6), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
    
    // Применяем основной цвет для тем аниме карточек
    document.documentElement.style.setProperty('--user-accent-color', color)
    
    // Применяем цвет к глобальным переменным для кнопок
    document.documentElement.style.setProperty('--accent', color)
    
    // Создаем более яркий цвет для hover состояния кнопок
    const hoverColor = lightenColor(color, 0.15)
    document.documentElement.style.setProperty('--accent-hover', hoverColor)
    
    // Создаем rgba версию для hover эффектов
    const rgba = rgbaColor(color, 0.1)
    document.documentElement.style.setProperty('--user-accent-color-rgba', rgba)
    
    // Создаем тень для text-shadow
    const shadowRgba = rgbaColor(color, 0.2)
    document.documentElement.style.setProperty('--user-accent-color-shadow', shadowRgba)
    
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
    
    // Создаем темный фон для идеальной оценки
    const hex = color.replace('#', '')
    const r = parseInt(hex.slice(0, 2), 16)
    const g = parseInt(hex.slice(2, 4), 16)
    const b = parseInt(hex.slice(4, 6), 16)
    const bgDark = `rgba(${Math.floor(r * 0.08)}, ${Math.floor(g * 0.08)}, ${Math.floor(b * 0.08)}, 0.95)`
    document.documentElement.style.setProperty('--user-accent-color-bg-dark', bgDark)
    
    // Создаем градиент для текста заголовков на основе цвета обводки аватарки
    const lightColor = lightenColor(color, 0.4)
    const darkColor = darkenColor(color, 0.2)
    const gradientText = `linear-gradient(135deg, ${lightColor} 0%, ${color} 50%, ${darkColor} 100%)`
    document.documentElement.style.setProperty('--user-gradient-text', gradientText)
    
    // Создаем градиент для подчеркивания заголовков
    const gradientUnderline = `linear-gradient(90deg, ${lightColor} 0%, ${color} 100%)`
    document.documentElement.style.setProperty('--user-gradient-underline', gradientUnderline)
    
    // Отправляем событие для обновления в других компонентах
    window.dispatchEvent(new Event('avatarBorderColorUpdated'))
  }

  const loadUserColors = async () => {
    // Настройки теперь загружаются через loadUserProfile из API
    // Эта функция оставлена для обратной совместимости, но теперь не используется
    if (username) {
      try {
        const response = await userAPI.getUserProfileSettings(username)
        if (response.message) {
          const settings = response.message
          const availableColorValues = AVAILABLE_COLORS.map(c => c.value)
          
          if (settings.username_color && availableColorValues.includes(settings.username_color)) {
            setUsernameColor(settings.username_color)
          }
          if (settings.avatar_border_color && availableColorValues.includes(settings.avatar_border_color)) {
            setAvatarBorderColor(settings.avatar_border_color)
            // Сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
            localStorage.setItem('user-avatar-border-color', settings.avatar_border_color)
            // Применяем цвет обводки аватарки к темам аниме карточек
            applyAvatarBorderColorToAnimeThemes(settings.avatar_border_color)
          }
        }
      } catch (err) {
        // Игнорируем ошибки, если настройки не найдены
        console.error('Ошибка загрузки настроек профиля:', err)
      }
    }
  }

  const loadPremiumProfile = async () => {
    // Премиум статус теперь загружается через loadUserProfile из API
    // Эта функция оставлена для обратной совместимости
    if (username && user) {
      // Дефолтное значение для пользователей с ID < 100
      if (user.id < 100) {
        setIsPremiumProfile(true)
      }
      
      try {
        const response = await userAPI.getUserProfileSettings(username)
        if (response.message && response.message.is_premium_profile !== undefined) {
          setIsPremiumProfile(response.message.is_premium_profile)
        }
      } catch (err) {
        // Игнорируем ошибки, если настройки не найдены
        console.error('Ошибка загрузки премиум статуса:', err)
      }
    }
  }

  const togglePremiumProfile = async () => {
    const newPremiumState = !isPremiumProfile
    setIsPremiumProfile(newPremiumState)
    
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          is_premium_profile: newPremiumState
        })
        
        // Если премиум выключен, применяем сохраненную тему профиля
        if (!newPremiumState && themeColor1 && themeColor2) {
          applyCustomTheme(themeColor1, themeColor2, gradientDirection || 'diagonal-right')
        } else if (!newPremiumState) {
          // Если премиум выключен и тема не установлена, сбрасываем на дефолтную
          document.documentElement.setAttribute('data-theme', 'dark')
          document.documentElement.style.removeProperty('--theme-color')
          document.documentElement.style.removeProperty('--theme-gradient')
          document.documentElement.style.removeProperty('--theme-gradient-reverse')
        }
        
        // Очищаем кэш профиля, чтобы при следующей загрузке использовались актуальные данные
        const CACHE_KEY = `user_profile_${username}`
        removeFromCache(CACHE_KEY)
      } catch (err) {
        console.error('Ошибка сохранения премиум профиля:', err)
        // Откатываем изменение при ошибке
        setIsPremiumProfile(!newPremiumState)
      }
    } else {
      console.warn('Cannot save premium profile: username is not available or not owner')
    }
  }

  const saveUsernameColor = async (color) => {
    // Разрешаем выбор любого цвета, включая 'premium' для золотого градиента
    setUsernameColor(color)
    
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          username_color: color
        })
      } catch (err) {
        console.error('Ошибка сохранения цвета имени:', err)
      }
    }
  }

  const saveAvatarBorderColor = async (color) => {
    setAvatarBorderColor(color)
    
    // СРАЗУ сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
    localStorage.setItem('user-avatar-border-color', color)
    
    // СРАЗУ применяем цвет к темам аниме карточек для любого пользователя
    applyAvatarBorderColorToAnimeThemes(color)
    
    // СРАЗУ обновляем все глобальные CSS переменные, если это профиль текущего пользователя
    // Используем функцию updateGlobalAccentColor из window (синхронная, применяет все переменные)
    if (username && currentUser && currentUser.username === username) {
      if (window.updateGlobalAccentColor) {
        // Используем глобальную функцию из App.jsx - она синхронная и применяет все переменные
        window.updateGlobalAccentColor(color)
      } else {
        // Если функция еще не загружена (маловероятно), применяем базовые переменные
        // и вызываем updateGlobalAccentColorIfCurrentUser для остальных
        const hex = color.replace('#', '')
        const r = parseInt(hex.slice(0, 2), 16)
        const g = parseInt(hex.slice(2, 4), 16)
        const b = parseInt(hex.slice(4, 6), 16)
        const rgba = `rgba(${r}, ${g}, ${b}, 0.1)`
        const shadowRgba = `rgba(${r}, ${g}, ${b}, 0.2)`
        
        document.documentElement.style.setProperty('--user-accent-color', color)
        document.documentElement.style.setProperty('--user-accent-color-rgba', rgba)
        document.documentElement.style.setProperty('--user-accent-color-shadow', shadowRgba)
        
        // Применяем остальные переменные (асинхронно, но не критично)
        updateGlobalAccentColorIfCurrentUser(color)
      }
    }
    
    // Сохраняем в API асинхронно (не блокируем UI)
    if (username && currentUser && currentUser.username === username) {
      try {
        await userAPI.updateProfileSettings({
          avatar_border_color: color
        })
        // Отправляем событие для обновления цвета в Layout
        window.dispatchEvent(new Event('avatarBorderColorUpdated'))
      } catch (err) {
        console.error('Ошибка сохранения цвета обводки аватарки:', err)
      }
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

  const loadUserProfile = async (forceReload = false) => {
    try {
      setLoading(true)
      setError(null)
      setAvatarError(false) // Сбрасываем ошибку аватарки при загрузке
      
      // Проверяем кэш профиля пользователя (TTL: 5 минут)
      const CACHE_KEY = `user_profile_${username}`
      const CACHE_TTL = 300 // 5 минут
      
      // Если требуется принудительная перезагрузка, очищаем кэш
      if (forceReload) {
        clearUserProfileCache(username)
      }
      
      const cachedData = getFromCache(CACHE_KEY)
      
      let response
      if (cachedData && !forceReload) {
        // Используем кэшированные данные
        response = { message: cachedData }
      } else {
        // Загружаем данные из API
        response = await userAPI.getUserProfile(username)
        // Сохраняем в кэш
        if (response?.message) {
          setToCache(CACHE_KEY, response.message, CACHE_TTL)
        }
      }
      
      if (response.message) {
        // Загружаем настройки профиля из ответа API ПЕРЕД установкой user
        let premiumStatus = false
        if (response.message.profile_settings) {
          const settings = response.message.profile_settings
          
          // Определяем премиум статус ПЕРВЫМ
          // Если явно установлен в настройках (включая false) - используем его
          // Иначе: для владельцев с ID < 25 премиум включен автоматически
          // Иначе: для пользователей с ID < 100 премиум по умолчанию
          if (settings.is_premium_profile !== undefined && settings.is_premium_profile !== null) {
            // Явно сохраненное значение имеет приоритет (даже если это false)
            premiumStatus = settings.is_premium_profile
          } else if (response.message.type_account === 'owner' && response.message.id < 25) {
            premiumStatus = true // Для владельцев с ID < 25 премиум включен автоматически
          } else {
            premiumStatus = response.message.id < 100 // Для пользователей с ID < 100 премиум по умолчанию
          }
          
          // Устанавливаем премиум статус сразу
          setIsPremiumProfile(premiumStatus)
          
          // Загружаем цвета независимо от премиум статуса
          // Если премиум включен и цвет не установлен, используем 'premium' по умолчанию
          if (settings.username_color) {
            setUsernameColor(settings.username_color)
          } else if (premiumStatus) {
            // Для премиум пользователей по умолчанию золотой градиент
            setUsernameColor('premium')
          }
          if (settings.avatar_border_color) {
            setAvatarBorderColor(settings.avatar_border_color)
            // Сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
            localStorage.setItem('user-avatar-border-color', settings.avatar_border_color)
            // Применяем цвет обводки аватарки к темам аниме карточек
            applyAvatarBorderColorToAnimeThemes(settings.avatar_border_color)
          }
          
          // Применяем тему профиля ТОЛЬКО если премиум выключен
          if (!premiumStatus && settings.theme_color_1 && settings.theme_color_2) {
            setThemeColor1(settings.theme_color_1)
            setThemeColor2(settings.theme_color_2)
            if (settings.gradient_direction) {
              setGradientDirection(settings.gradient_direction)
            }
            // Применяем тему сразу, пока не установили user
            applyCustomTheme(
              settings.theme_color_1,
              settings.theme_color_2,
              settings.gradient_direction || 'diagonal-right'
            )
          } else if (settings.theme_color_1 && settings.theme_color_2) {
            // Сохраняем настройки темы, но не применяем если премиум активен
            setThemeColor1(settings.theme_color_1)
            setThemeColor2(settings.theme_color_2)
            if (settings.gradient_direction) {
              setGradientDirection(settings.gradient_direction)
            }
          }
        } else {
          // Если настроек нет, используем дефолтные значения
          // Для владельцев с ID < 25 премиум включен автоматически
          if (response.message.type_account === 'owner' && response.message.id < 25) {
            premiumStatus = true
          } else {
            premiumStatus = response.message.id < 100
          }
          setIsPremiumProfile(premiumStatus)
          // Если премиум включен, устанавливаем золотой градиент по умолчанию
          if (premiumStatus) {
            setUsernameColor('premium')
          }
        }
        
        // Устанавливаем user ПОСЛЕ применения всех настроек
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
          className={`profile-header ${isPremiumProfile ? 'premium-header' : ''}`}
          style={isPremiumProfile ? undefined : {
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
                    {(isPremiumProfile || (user && (user.type_account === 'owner' || user.type_account === 'admin'))) && (
                      <button
                        key="premium"
                        className={`color-button ${usernameColor === 'premium' ? 'active' : ''}`}
                        style={{ 
                          background: 'linear-gradient(135deg, #ffc800 0%, #fff200 25%, #ffd700 50%, #fff200 75%, #ffc800 100%)'
                        }}
                        onClick={() => saveUsernameColor('premium')}
                        title="Золотой градиент"
                        aria-label="Золотой градиент"
                      >
                        {usernameColor === 'premium' && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </button>
                    )}
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
                <div className="theme-color-group">
                  <label>Градиент темы сайта:</label>
                  <div className="theme-color-buttons">
                    <button
                      className={`theme-color-reset-btn ${themeColor1 === null ? 'active' : ''}`}
                      onClick={handleResetTheme}
                      title="Темная тема по умолчанию"
                      disabled={isPremiumProfile}
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
                          disabled={isPremiumProfile}
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
                          disabled={isPremiumProfile}
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
                          disabled={isPremiumProfile}
                        >
                          {dir.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  {isPremiumProfile && (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      Недоступно при активном премиум профиле
                    </p>
                  )}
                </div>
                <div className="premium-profile-group">
                  <label>Премиум оформление:</label>
                  <button
                    className={`premium-profile-toggle ${isPremiumProfile ? 'active' : ''}`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      togglePremiumProfile()
                    }}
                    type="button"
                  >
                    <span className="premium-toggle-label">
                      {isPremiumProfile ? '✓ Премиум профиль активен' : 'Премиум профиль'}
                    </span>
                    {isPremiumProfile && (
                      <CrownIcon size={20} />
                    )}
                  </button>
                  <p className="premium-profile-description">
                    {user && user.id < 25 
                      ? 'Вы один из первых 25 пользователей - можете включать/отключать премиум оформление'
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
              
              if (avatarUrl && !avatarError) {
                return (
                  <img 
                    src={avatarUrl} 
                    alt={user.username}
                    className={`profile-avatar ${isPremiumProfile ? 'premium-avatar' : ''}`}
                    style={isPremiumProfile ? undefined : { 
                      borderColor: avatarBorderColor,
                      boxShadow: `0 8px 24px ${hexToRgba(avatarBorderColor, 0.3)}`
                    }}
                    onError={(e) => {
                      // Останавливаем повторные попытки загрузки
                      e.target.src = ''
                      setAvatarError(true)
                    }}
                    onLoad={() => {
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
                    className={`profile-avatar profile-avatar-fallback ${isPremiumProfile ? 'premium-avatar' : ''}`}
                    style={isPremiumProfile ? {
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
              className={`profile-username ${
                usernameColor === 'premium' 
                  ? 'premium-user' 
                  : (user && (user.type_account === 'owner' || user.type_account === 'admin' || user.type_account === 'premium'))
                    ? 'premium-shine'
                    : ''
              }`}
              style={usernameColor === 'premium' ? undefined : { 
                color: usernameColor
              }}
              data-premium={usernameColor === 'premium'}
              data-text={
                usernameColor === 'premium' || (user && (user.type_account === 'owner' || user.type_account === 'admin' || user.type_account === 'premium'))
                  ? user.username 
                  : ''
              }
            >
              {user.username}
              {user.id < 25 && (
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
                
                if (user.id < 25) {
                  allBadges.push({
                    id: 'premium',
                    element: (
                      <span key="premium" className="profile-role profile-premium-badge">
                        Один из 25
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
                
                // Бэйдж с топ-1 аниме пользователя
                const topAnime = bestAnime.find(anime => anime.place === 1)
                if (topAnime && topAnime.title) {
                  // Создаем градиент на основе цвета обводки аватарки
                  const badgeGradient = createGradientFromColor(avatarBorderColor)
                  const badgeShadow = hexToRgba(avatarBorderColor, 0.5)
                  const badgeShadowLight = hexToRgba(avatarBorderColor, 0.3)
                  const badgeTextShadow = hexToRgba(avatarBorderColor, 0.6)
                  
                  allBadges.push({
                    id: 'top-anime',
                    element: (
                      <span 
                        key="top-anime" 
                        className="profile-role profile-top-anime-badge"
                        style={{
                          background: `linear-gradient(135deg, rgba(26, 26, 26, 0.8) 0%, rgba(20, 20, 20, 0.8) 100%) padding-box, ${badgeGradient} border-box`,
                          borderColor: 'transparent',
                          color: avatarBorderColor,
                          boxShadow: `0 4px 16px ${badgeShadow}, 0 0 24px ${badgeShadowLight}, 0 0 40px ${badgeShadowLight}`,
                          textShadow: `0 0 8px ${badgeTextShadow}, 0 0 16px ${badgeShadow}`
                        }}
                      >
                        {topAnime.title}
                      </span>
                    )
                  })
                }
                
                // Бейдж "Коллекционер #1"
                const hasCollectorBadge = user.profile_settings?.has_collector_badge || false
                if (hasCollectorBadge) {
                  allBadges.push({
                    id: 'collector-badge',
                    element: (
                      <span 
                        key="collector-badge" 
                        className="profile-role profile-collector-badge"
                        style={{
                          background: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 25%, #ffd700 50%, #ffed4e 75%, #ffd700 100%)',
                          backgroundSize: '200% 200%',
                          animation: 'gold-shimmer 3s ease-in-out infinite',
                          color: '#000',
                          fontWeight: '700',
                          boxShadow: '0 4px 16px rgba(255, 215, 0, 0.6), 0 0 24px rgba(255, 215, 0, 0.4)',
                          textShadow: 'none'
                        }}
                      >
                        Коллекционер #1
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

        <div className={`profile-stats ${isPremiumProfile ? 'premium-stats' : ''}`}>
          <Link 
            to={`/profile/${username}/favorites`}
            className="stat-card" 
            style={isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3),
              cursor: 'pointer',
              textDecoration: 'none'
            }}
          >
            <div className="stat-value" style={isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.favorites_count}</div>
            <div className={`stat-label ${isPremiumProfile ? 'premium-label' : ''}`}>Избранное</div>
          </Link>
          <div 
            className="stat-card" 
            style={isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.ratings_count}</div>
            <div className={`stat-label ${isPremiumProfile ? 'premium-label' : ''}`}>Оценок</div>
          </div>
          <div 
            className="stat-card" 
            style={isPremiumProfile ? undefined : { 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3)
            }}
          >
            <div className="stat-value" style={isPremiumProfile ? undefined : { color: avatarBorderColor }}>{stats.comments_count}</div>
            <div className={`stat-label ${isPremiumProfile ? 'premium-label' : ''}`}>Комментариев</div>
          </div>
        </div>

        <BestAnimeSection
          bestAnime={bestAnime}
          favorites={favoritesAnime}
          isOwner={isOwner}
          onUpdate={() => loadUserProfile(true)}
          avatarBorderColor={avatarBorderColor}
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
            className={user && isPremiumProfile ? 'premium-anime-grid' : ''}
            sortCriteria="Аниме, добавленные вами в избранное."
          />
        ) : (
          <section className="popular-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <div className="sort-info-tooltip">
                  <span className="tooltip-icon">?</span>
                  <div className="tooltip-content">
                    Аниме, добавленные вами в избранное.
                  </div>
                </div>
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

import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import { getFromCache, setToCache, removeFromCache, clearUserProfileCache } from '../utils/cache'
import AnimeGrid from '../components/AnimeGrid'
import CrownIcon from '../components/CrownIcon'
import BestAnimeSection from '../components/BestAnimeSection'
import QRModal from '../components/QRModal'
import '../components/AnimeCardGrid.css'
import './UserProfilePage.css'
import '../pages/HomePage.css'
import './AnimeMerchPage.css'

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
  const [avatarError, setAvatarError] = useState(false)
  const [backgroundImageUrl, setBackgroundImageUrl] = useState(null)
  const [backgroundSettings, setBackgroundSettings] = useState({
    scale: 100,
    positionX: 50,
    positionY: 50
  })
  const [panelPosition, setPanelPosition] = useState({ top: 0, right: 0 })
  const [isQRModalOpen, setIsQRModalOpen] = useState(false)
  const settingsIconRef = useRef(null)
  const itemsPerPage = 6
  const maxPagesToShow = 3
  
  // Проверяем, является ли текущий пользователь владельцем профиля
  const isOwner = currentUser && user && currentUser.username === user.username
  

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
    
    // Обработчик обновления фонового изображения
    const handleBackgroundImageUpdated = (event) => {
      const { username: updatedUsername, backgroundImageUrl: newUrl, settings } = event.detail
      if (updatedUsername === username) {
        // Если newUrl равен null или undefined, удаляем фоновое изображение
        setBackgroundImageUrl(newUrl || null)
        if (settings) {
          setBackgroundSettings({
            scale: settings.scale || 100,
            positionX: settings.positionX || 50,
            positionY: settings.positionY || 50
          })
        } else {
          // Сбрасываем настройки на значения по умолчанию при удалении
          setBackgroundSettings({
            scale: 100,
            positionX: 50,
            positionY: 50
          })
        }
        // Перезагружаем профиль для получения актуальных данных
        loadUserProfile()
      }
    }
    
    // Обработчик обновления аватарки
    const handleAvatarUpdated = async (event) => {
      const eventData = event?.detail
      const updatedUsername = eventData?.username
      const newAvatarUrl = eventData?.avatarUrl
      
      // Проверяем, относится ли обновление к текущему профилю
      if (updatedUsername === username) {
        
        // Сбрасываем ошибку аватарки
        setAvatarError(false)
        
        // Очищаем кэш профиля и перезагружаем данные
        clearUserProfileCache(username)
        await loadUserProfile(true)
      }
    }
    
    // Обработчик изменений localStorage (для синхронизации между вкладками)
    const handleStorageChange = (e) => {
      if (e.key === 'avatarUpdated' && e.newValue) {
        try {
          const data = JSON.parse(e.newValue)
          if (data.username === username && data.avatarUrl) {
            setAvatarError(false)
            clearUserProfileCache(username)
            loadUserProfile(true)
            // Удаляем запись из localStorage после обработки
            localStorage.removeItem('avatarUpdated')
          }
        } catch (err) {
          console.error('Ошибка обработки данных из localStorage:', err)
        }
      }
    }
    
    // Проверяем localStorage при монтировании компонента
    const checkLocalStorage = () => {
      try {
        const stored = localStorage.getItem('avatarUpdated')
        if (stored) {
          const data = JSON.parse(stored)
          if (data.username === username && data.avatarUrl && data.timestamp && Date.now() - data.timestamp < 5 * 60 * 1000) {
            setAvatarError(false)
            clearUserProfileCache(username)
            loadUserProfile(true)
            localStorage.removeItem('avatarUpdated')
          } else if (data.timestamp && Date.now() - data.timestamp >= 5 * 60 * 1000) {
            // Удаляем устаревшие данные
            localStorage.removeItem('avatarUpdated')
          }
        }
      } catch (err) {
        console.error('Ошибка проверки localStorage:', err)
      }
    }
    
    // Проверяем localStorage при монтировании
    checkLocalStorage()
    
    window.addEventListener('cacheRemoved', handleCacheRemoved)
    window.addEventListener('backgroundImageUpdated', handleBackgroundImageUpdated)
    window.addEventListener('avatarUpdated', handleAvatarUpdated)
    window.addEventListener('storage', handleStorageChange)
    
    // При уходе со страницы профиля восстанавливаем цвета текущего авторизованного пользователя
    return async () => {
      window.removeEventListener('cacheRemoved', handleCacheRemoved)
      window.removeEventListener('backgroundImageUpdated', handleBackgroundImageUpdated)
      window.removeEventListener('avatarUpdated', handleAvatarUpdated)
      window.removeEventListener('storage', handleStorageChange)
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

  // Вычисляем позицию панели настроек относительно иконки
  useEffect(() => {
    if (showSettings && settingsIconRef.current) {
      const updatePosition = () => {
        const iconRect = settingsIconRef.current.getBoundingClientRect()
        setPanelPosition({
          top: iconRect.bottom + 10,
          right: window.innerWidth - iconRect.right
        })
      }
      
      updatePosition()
      window.addEventListener('resize', updatePosition)
      window.addEventListener('scroll', updatePosition, true)
      
      return () => {
        window.removeEventListener('resize', updatePosition)
        window.removeEventListener('scroll', updatePosition, true)
      }
    }
  }, [showSettings])

  // Отладка: проверяем применение стилей фона и доступность изображения
  useEffect(() => {
    if (backgroundImageUrl) {
      // Проверяем доступность изображения
      const img = new Image()
      img.onload = () => {
      }
      img.onerror = () => {
        console.error('❌ Background image failed to load (404 or other error):', backgroundImageUrl)
        console.warn('⚠️ Проверьте, что файл существует в S3 хранилище по указанному пути')
      }
      img.src = backgroundImageUrl
      
      // Проверяем элемент в DOM
      setTimeout(() => {
        const headerElement = document.querySelector('.profile-header')
        if (headerElement) {
          const headerStyle = getComputedStyle(headerElement)
          // Проверяем псевдоэлемент ::before
          const beforeStyle = getComputedStyle(headerElement, '::before')
          
            inlineStyle: {
              bgImage: headerElement.style.getPropertyValue('--bg-image'),
              bgSize: headerElement.style.getPropertyValue('--bg-size'),
              bgPosition: headerElement.style.getPropertyValue('--bg-position')
            },
            computedStyle: {
              backgroundImage: headerStyle.backgroundImage,
              backgroundSize: headerStyle.backgroundSize,
              backgroundPosition: headerStyle.backgroundPosition
            },
            beforePseudoElement: {
              backgroundImage: beforeStyle.backgroundImage,
              backgroundSize: beforeStyle.backgroundSize,
              backgroundPosition: beforeStyle.backgroundPosition,
              content: beforeStyle.content,
              display: beforeStyle.display,
              zIndex: beforeStyle.zIndex
            },
            cssVariables: {
              bgImage: headerStyle.getPropertyValue('--bg-image'),
              bgSize: headerStyle.getPropertyValue('--bg-size'),
              bgPosition: headerStyle.getPropertyValue('--bg-position')
            },
            dataUrl: headerElement.querySelector('.profile-avatar-section')?.dataset.backgroundUrl
          })
          
          // Проверяем, что фон применяется к псевдоэлементу
          if (beforeStyle.backgroundImage === 'none' || !beforeStyle.backgroundImage.includes('url')) {
            console.warn('⚠️ Псевдоэлемент ::before не имеет фонового изображения!')
            console.warn('Проверьте, что CSS переменные применяются правильно')
            console.warn('CSS переменная --bg-image:', headerStyle.getPropertyValue('--bg-image'))
          } else {
          }
        }
      }, 200)
    }
  }, [backgroundImageUrl, backgroundSettings])

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
          // Загружаем настройки отображения фонового изображения
          setBackgroundSettings({
            scale: settings.background_scale || 100,
            positionX: settings.background_position_x || 50,
            positionY: settings.background_position_y || 50
          })
        }
      } catch (err) {
        // Игнорируем ошибки, если настройки не найдены
        console.error('Ошибка загрузки настроек профиля:', err)
      }
    }
  }

  const saveUsernameColor = async (color) => {
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
      
      // Проверяем кэш профиля пользователя (TTL: 1 час - синхронизировано с backend)
      const CACHE_KEY = `user_profile_${username}`
      const CACHE_TTL = 3600 // 1 час (3600 секунд) - синхронизировано с backend
      
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
        if (response.message.profile_settings) {
          const settings = response.message.profile_settings
          
          // Загружаем цвета
          if (settings.username_color) {
            setUsernameColor(settings.username_color)
          }
          if (settings.avatar_border_color) {
            setAvatarBorderColor(settings.avatar_border_color)
            // Сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
            localStorage.setItem('user-avatar-border-color', settings.avatar_border_color)
            // Применяем цвет обводки аватарки к темам аниме карточек
            applyAvatarBorderColorToAnimeThemes(settings.avatar_border_color)
          }
          
          // Загружаем настройки отображения фонового изображения
          setBackgroundSettings({
            scale: settings.background_scale !== undefined && settings.background_scale !== null 
              ? settings.background_scale 
              : 100,
            positionX: settings.background_position_x !== undefined && settings.background_position_x !== null 
              ? settings.background_position_x 
              : 50,
            positionY: settings.background_position_y !== undefined && settings.background_position_y !== null 
              ? settings.background_position_y 
              : 50
          })
        }
        
        // Устанавливаем user ПОСЛЕ применения всех настроек
        setUser(response.message)
        
        // Загружаем URL фонового изображения из user
        if (response.message.background_image_url) {
          setBackgroundImageUrl(response.message.background_image_url)
        } else {
          setBackgroundImageUrl(null)
        }
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
      <div className="anime-merch-page">
        <div className="anime-merch-container">
          <img 
            src="/anime-merch.png" 
            alt="Пользователь не найден" 
            className="anime-merch-image"
          />
          <h2 className="anime-merch-404">404 - Not Found</h2>
          <p className="anime-merch-message">Пользователь не найден</p>
          <button 
            className="anime-merch-button"
            onClick={() => setIsQRModalOpen(true)}
          >
            Ускорить разработку
          </button>
        </div>
        <QRModal 
          isOpen={isQRModalOpen} 
          onClose={() => setIsQRModalOpen(false)} 
        />
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
          className="profile-header"
          style={{
            borderColor: avatarBorderColor,
            boxShadow: `0 8px 48px ${hexToRgba(avatarBorderColor, 0.4)}, 0 0 0 1px ${avatarBorderColor}`,
            ...(backgroundImageUrl ? {
              '--bg-image': `url("${backgroundImageUrl}")`,
              '--bg-size': `${backgroundSettings.scale}%`,
              '--bg-position': `${backgroundSettings.positionX}% ${backgroundSettings.positionY}%`
            } : {
              '--bg-image': 'none'
            })
          }}
        >
          {isOwner && (
            <>
              <div 
                ref={settingsIconRef}
                className="profile-settings-icon" 
                onClick={() => setShowSettings(!showSettings)}
              >
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
            </>
          )}

          <div 
            className="profile-avatar-section"
            style={{
              backgroundImage: backgroundImageUrl ? `url("${backgroundImageUrl}")` : 'none',
              backgroundSize: `${backgroundSettings.scale}%`,
              backgroundPosition: `${backgroundSettings.positionX}% ${backgroundSettings.positionY}%`,
              backgroundRepeat: 'no-repeat',
              backgroundAttachment: 'local',
              '--avatar-border-color': avatarBorderColor,
              '--avatar-glow-color': hexToRgba(avatarBorderColor, 0.4)
            }}
            data-background-url={backgroundImageUrl}
            data-background-scale={backgroundSettings.scale}
          >
            {(() => {
              const avatarUrl = normalizeAvatarUrl(user.avatar_url)
              
              if (avatarUrl && !avatarError) {
                return (
                  <img 
                    src={avatarUrl} 
                    alt={user.username}
                    className="profile-avatar"
                    style={{ 
                      borderColor: avatarBorderColor
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
                return (
                  <div 
                    className="profile-avatar profile-avatar-fallback"
                    style={{
                      width: '150px',
                      height: '150px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: 'transparent',
                      borderColor: avatarBorderColor,
                      border: `3px solid ${avatarBorderColor}`,
                      borderRadius: '50%',
                      position: 'relative',
                      zIndex: 2,
                      boxShadow: `0 8px 48px ${hexToRgba(avatarBorderColor, 0.4)}`
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
                (user && (user.type_account === 'owner' || user.type_account === 'admin'))
                  ? 'premium-shine'
                  : ''
              }`}
              style={{ 
                color: usernameColor
              }}
              data-text={
                (user && (user.type_account === 'owner' || user.type_account === 'admin'))
                  ? user.username 
                  : ''
              }
            >
              {user.username}
              {(user?.premium_status?.is_premium || user?.profile_settings?.is_premium_profile || user.type_account === 'admin' || user.type_account === 'owner') && (
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
                        {user.type_account === 'base' ? 'Базовый' : user.type_account}
                      </span>
                    )
                  })
                }
                
                if (user.id <= 5) {
                  allBadges.push({
                    id: 'premium',
                    element: (
                      <span key="premium" className="profile-role profile-premium-badge">
                        Один из 5
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

        {/* Панель настроек вне profile-header, чтобы не обрезалась overflow: hidden */}
        {isOwner && showSettings && (
          <div 
            className="profile-settings-panel"
            style={{
              top: `${panelPosition.top}px`,
              right: `${panelPosition.right}px`
            }}
          >
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

        <div className="profile-stats">
          <Link 
            to={`/profile/${username}/favorites`}
            className="stat-card" 
            style={{ 
              '--stat-color': avatarBorderColor,
              '--stat-color-shadow': hexToRgba(avatarBorderColor, 0.3),
              cursor: 'pointer',
              textDecoration: 'none'
            }}
          >
            <div className="stat-value" style={{ color: avatarBorderColor }}>{stats.favorites_count}</div>
            <div className="stat-label">Избранное</div>
          </Link>
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
            className=""
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

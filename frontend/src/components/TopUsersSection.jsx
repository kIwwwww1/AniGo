import { useState, useEffect, useRef, memo, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate, Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import { getInitials, getColorFromUsername, normalizeAvatarUrl } from '../utils/avatarUtils'
import { getFromCache, setToCache, removeFromCache } from '../utils/cache'
import CrownIcon from './CrownIcon'
import './TopUsersSection.css'

const AVAILABLE_COLORS = [
  '#ffffff', '#000000', '#808080', '#c4c4af', 
  '#0066ff', '#00cc00', '#ff0000', '#ff69b4', 
  '#ffd700', '#9932cc'
]

const USERS_PER_PAGE = 3
const MAX_USERS = 6
const CACHE_KEY = 'top_users_most_favorited'
const CACHE_TTL = 900 // 15 минут в секундах
const UPDATE_INTERVAL = 15 * 60 * 1000 // 15 минут в миллисекундах

const TopUsersSection = memo(function TopUsersSection() {
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [isScrolling, setIsScrolling] = useState(false)
  const [avatarErrors, setAvatarErrors] = useState({}) // Состояние для отслеживания ошибок загрузки аватарок
  const [backgroundImageErrors, setBackgroundImageErrors] = useState({}) // Состояние для отслеживания ошибок загрузки фоновых изображений
  const [cycleInfo, setCycleInfo] = useState(null) // Информация о текущем цикле конкурса
  const [isActiveWeek, setIsActiveWeek] = useState(false) // Активна ли неделя конкурса
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0, visible: false })
  const carouselRef = useRef(null)
  const loadTopUsersRef = useRef(null)
  const currentUserRef = useRef({ username: null, avatarUrl: null })
  const updateIntervalRef = useRef(null) // Ref для интервала обновления
  const tooltipRef = useRef(null)
  const trophyRef = useRef(null)
  const usersRef = useRef([]) // Ref для хранения текущего списка пользователей

  // Функция для создания градиента на основе цветов профиля
  const createThemeGradient = (color1, color2, direction = 'diagonal-right') => {
    if (!color1 || !color2) return null
    
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
    
    const hexToRgba = (hex, alpha) => {
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
    
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
    
    const lightBg1 = lightenColor(color1, 0.3)
    const lightBg2 = lightenColor(color2, 0.3)
    
    const mix1 = mixColors(color1, color2, 0.2)
    const mix2 = mixColors(color1, color2, 0.4)
    const mix3 = mixColors(color1, color2, 0.5)
    const mix4 = mixColors(color1, color2, 0.6)
    const mix5 = mixColors(color1, color2, 0.8)
    
    const rgba1 = hexToRgba(color1, 0.4)
    const rgba2 = hexToRgba(color2, 0.4)
    const rgba1Light = hexToRgba(lightBg1, 0.3)
    const rgba2Light = hexToRgba(lightBg2, 0.3)
    
    const rgbaMix1 = hexToRgba(mix1, 0.38)
    const rgbaMix2 = hexToRgba(mix2, 0.37)
    const rgbaMix3 = hexToRgba(mix3, 0.36)
    const rgbaMix4 = hexToRgba(mix4, 0.37)
    const rgbaMix5 = hexToRgba(mix5, 0.38)
    
    let gradientString = ''
    if (direction === 'radial') {
      gradientString = `radial-gradient(circle, ${rgba1Light} 0%, ${rgba1} 12%, ${rgbaMix1} 25%, ${rgbaMix2} 37%, ${rgbaMix3} 50%, ${rgbaMix4} 62%, ${rgbaMix5} 75%, ${rgba2} 88%, ${rgba2Light} 100%)`
    } else {
      let angle = '135deg'
      if (direction === 'horizontal') angle = 'to right'
      else if (direction === 'vertical') angle = 'to bottom'
      else if (direction === 'diagonal-right') angle = '135deg'
      else if (direction === 'diagonal-left') angle = '45deg'
      
      gradientString = `linear-gradient(${angle}, ${rgba1Light} 0%, ${rgba1} 5%, ${rgbaMix1} 12%, ${rgbaMix2} 20%, ${rgbaMix3} 30%, ${rgbaMix4} 42%, ${rgbaMix5} 55%, ${rgba2} 68%, ${rgba2Light} 80%, ${rgba2} 90%, ${rgba2Light} 100%)`
    }
    
    return gradientString
  }

  // Функция для обработки данных пользователей БЕЗ обновления градиентов (используется при загрузке из кэша)
  const processUsersDataWithoutGradients = (usersData, existingUsers = []) => {
    if (!usersData || !Array.isArray(usersData) || usersData.length === 0) {
      return []
    }
    
    // Ограничиваем до MAX_USERS пользователей
    const limitedUsersData = usersData.slice(0, MAX_USERS)
    
    // Обрабатываем данные без обновления градиентов - сохраняем существующие градиенты из состояния
    return limitedUsersData.map(user => {
      // Находим существующего пользователя в текущем состоянии для сохранения градиента
      const existingUser = existingUsers.find(u => u.username === user.username)
      
      // Используем настройки профиля из данных кэша
      const settings = user.profile_settings || {}
      const isPremium = settings.is_premium_profile !== undefined 
        ? settings.is_premium_profile 
        : (user.id < 100)
      
      // Если премиум включен, используем золотой цвет
      if (isPremium) {
        return {
          ...user,
          accentColor: '#ffd700',
          isPremium: true,
          themeGradient: null,
          usernameColor: 'premium' // Для премиум используем специальное значение
        }
      }
      
      // Иначе используем цвет обводки аватарки из настроек профиля
      const userColor = settings.avatar_border_color && AVAILABLE_COLORS.includes(settings.avatar_border_color)
        ? settings.avatar_border_color
        : '#e50914'
      
      // Получаем цвет никнейма из настроек профиля
      const usernameColor = settings.username_color && /^#[0-9A-Fa-f]{6}$/.test(settings.username_color)
        ? settings.username_color
        : '#ffffff' // Белый по умолчанию
      
      // Если есть существующий градиент, сохраняем его
      // Если нет существующего градиента, но есть настройки в данных кэша - создаем градиент из них
      // Это нужно для первой загрузки, когда existingUsers пустой
      let themeGradient = existingUser?.themeGradient || null
      
      if (!themeGradient) {
        // Создаем градиент ТОЛЬКО из theme_color_1 и theme_color_2 из БД
        // Не используем avatar_border_color для создания градиента
        if (settings.theme_color_1 && settings.theme_color_2) {
          // Проверяем, что цвета валидные hex-цвета
          const color1Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_1)
          const color2Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_2)
          
          if (color1Valid && color2Valid) {
            const gradientDirection = settings.gradient_direction || 'diagonal-right'
            themeGradient = createThemeGradient(settings.theme_color_1, settings.theme_color_2, gradientDirection)
          }
        }
      }
      
      return {
        ...user,
        accentColor: userColor,
        isPremium: false,
        themeGradient: themeGradient,
        usernameColor: usernameColor
      }
    })
  }

  // Функция для обработки данных пользователей (вынесена для переиспользования)
  const processUsersData = (usersData) => {
    if (!usersData || !Array.isArray(usersData) || usersData.length === 0) {
      return []
    }
    
    // Ограничиваем до MAX_USERS пользователей
    const limitedUsersData = usersData.slice(0, MAX_USERS)
    
    // Загружаем настройки профиля для каждого пользователя из API
    return limitedUsersData.map(user => {
      // Используем настройки профиля из API
      const settings = user.profile_settings || {}
      const isPremium = settings.is_premium_profile !== undefined 
        ? settings.is_premium_profile 
        : (user.id < 100) // Для пользователей с ID < 100 премиум по умолчанию
      
      // Если премиум включен, используем золотой цвет
      if (isPremium) {
        return {
          ...user,
          accentColor: '#ffd700', // Золотой цвет для премиум
          isPremium: true,
          themeGradient: null, // Премиум не использует градиент, использует золотую обводку
          usernameColor: 'premium' // Для премиум используем специальное значение
        }
      }
      
      // Иначе используем цвет обводки аватарки из настроек профиля
      const userColor = settings.avatar_border_color && AVAILABLE_COLORS.includes(settings.avatar_border_color)
        ? settings.avatar_border_color
        : '#e50914' // Цвет по умолчанию
      
      // Получаем цвет никнейма из настроек профиля
      const usernameColor = settings.username_color && /^#[0-9A-Fa-f]{6}$/.test(settings.username_color)
        ? settings.username_color
        : '#ffffff' // Белый по умолчанию
      
      // Создаем градиент ТОЛЬКО из theme_color_1 и theme_color_2 из БД
      // Не используем avatar_border_color для создания градиента
      let themeGradient = null
      if (settings.theme_color_1 && settings.theme_color_2) {
        // Проверяем, что цвета валидные hex-цвета
        const color1Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_1)
        const color2Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_2)
        
        if (color1Valid && color2Valid) {
          const gradientDirection = settings.gradient_direction || 'diagonal-right'
          themeGradient = createThemeGradient(settings.theme_color_1, settings.theme_color_2, gradientDirection)
        }
      }
      
      return {
        ...user,
        accentColor: userColor,
        isPremium: false,
        themeGradient: themeGradient,
        usernameColor: usernameColor
      }
    })
  }

  const loadTopUsers = async (skipCache = false, updateGradients = false) => {
    try {
      setLoading(true)
      setError(null)
      setAvatarErrors({}) // Сбрасываем ошибки аватарок при загрузке
      
      // Проверяем кэш только если не пропущен
      if (!skipCache) {
        const cachedData = getFromCache(CACHE_KEY)
        if (cachedData) {
          // Проверяем, что данные в кэше корректны (есть хотя бы один пользователь с avatar_url)
          // Если все пользователи без avatar_url, возможно кэш устарел
          const hasUsersWithAvatars = cachedData.some && cachedData.some(user => user.avatar_url)
          
          // Проверяем, есть ли в кэше актуальные настройки профиля с градиентами
          // Если у всех пользователей theme_color_1 и theme_color_2 равны null, возможно кэш устарел
          const hasUsersWithGradients = cachedData.some && cachedData.some(user => {
            const settings = user.profile_settings || {}
            return settings.theme_color_1 && settings.theme_color_2
          })
          
          if (hasUsersWithAvatars || cachedData.length === 0) {
            // Если нужно обновить градиенты или их нет в кэше, загружаем из API
            if (updateGradients || !hasUsersWithGradients) {
              // Очищаем кэш и продолжаем загрузку из API
              removeFromCache(CACHE_KEY)
              // Продолжаем выполнение, чтобы загрузить данные из API
            } else {
              // Данные в кэше выглядят корректно, используем их
              setUsers(prevUsers => {
                const usersWithColors = processUsersDataWithoutGradients(cachedData, prevUsers)
                usersRef.current = usersWithColors // Обновляем ref
                return usersWithColors
              })
              
              // Делаем запрос только за информацией о цикле, если данные из кэша
              // Это необходимо для установки интервала обновления
              try {
                const response = await userAPI.getMostFavoritedUsers(MAX_USERS, 0)
                const cycleInfoData = response.cycle_info || null
                setCycleInfo(cycleInfoData)
                
                // Определяем, активна ли неделя конкурса
                let activeWeek = false
                if (cycleInfoData && cycleInfoData.is_active) {
                  const cycleEndDate = new Date(cycleInfoData.cycle_end_date)
                  const now = new Date()
                  activeWeek = cycleEndDate > now
                }
                setIsActiveWeek(activeWeek)
              } catch (err) {
                console.warn('Не удалось получить информацию о цикле:', err)
              }
              
              setLoading(false)
              return
            }
          } else {
            // Данные в кэше выглядят устаревшими (все пользователи без аватарок)
            // Очищаем кэш и загружаем свежие данные
            removeFromCache(CACHE_KEY)
            skipCache = true
          }
        }
      }
      
      // Кэш отсутствует или истек, запрашиваем данные из API
      const response = await userAPI.getMostFavoritedUsers(MAX_USERS, 0)
      
      // API возвращает {'users': [...], 'cycle_info': {...}}
      let usersData = []
      if (response.users && Array.isArray(response.users)) {
        usersData = response.users
      } else if (Array.isArray(response.message)) {
        // Обратная совместимость со старым форматом
        usersData = response.message
      } else {
        usersData = []
      }
      
      // Получаем информацию о цикле из ответа
      const cycleInfoData = response.cycle_info || null
      setCycleInfo(cycleInfoData)
      
      // Определяем, активна ли неделя конкурса
      let activeWeek = false
      if (cycleInfoData && cycleInfoData.is_active) {
        const cycleEndDate = new Date(cycleInfoData.cycle_end_date)
        const now = new Date()
        activeWeek = cycleEndDate > now
      }
      setIsActiveWeek(activeWeek)
      
      // Обрабатываем данные - всегда обновляем градиенты при загрузке из API
      const usersWithColors = processUsersData(usersData)
      
      // Сохраняем в кэш на 15 минут
      setToCache(CACHE_KEY, usersData, CACHE_TTL)
      
      setUsers(usersWithColors)
      usersRef.current = usersWithColors // Обновляем ref
    } catch (err) {
      console.error('Ошибка загрузки топ пользователей:', err)
      setError(err.response?.data?.detail || err.message || 'Ошибка загрузки пользователей')
    } finally {
      setLoading(false)
    }
  }

  // Сохраняем ссылку на функцию в ref
  useEffect(() => {
    loadTopUsersRef.current = loadTopUsers
  })

  useEffect(() => {
    loadTopUsers()
    
    // Очистка интервала при размонтировании
    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current)
        updateIntervalRef.current = null
      }
    }
  }, [])
  
  // Эффект для автоматического обновления каждые 15 минут
  useEffect(() => {
    // Устанавливаем интервал обновления
    const setupInterval = () => {
      if (loadTopUsersRef.current) {
        // Устанавливаем интервал обновления на 15 минут
        updateIntervalRef.current = setInterval(() => {
          if (loadTopUsersRef.current) {
            // Обновляем данные и градиенты вместе при периодическом обновлении
            // Всегда пропускаем кэш для периодического обновления
            loadTopUsersRef.current(true, true) // Пропускаем кэш и обновляем градиенты
          }
        }, UPDATE_INTERVAL)
      }
    }
    
    // Пытаемся установить интервал сразу
    setupInterval()
    
    // Если не удалось (функция еще не загружена), пробуем через небольшую задержку
    let timeoutId = null
    if (!updateIntervalRef.current) {
      timeoutId = setTimeout(() => {
        setupInterval()
      }, 100)
    }
    
    // Очистка при размонтировании
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current)
        updateIntervalRef.current = null
      }
    }
  }, []) // Устанавливаем интервал только один раз при монтировании компонента

  // Обработчик удаления кэша - автоматическая перезагрузка данных
  useEffect(() => {
    const handleCacheRemoved = (event) => {
      const removedKey = event?.detail?.key
      
      // Проверяем, относится ли удаленный кэш к нашему компоненту
      // Поддерживаем разные варианты ключей
      const keyMatches = 
        removedKey === CACHE_KEY || 
        removedKey === 'top_users' || 
        removedKey === 'top_users_most_favorited' ||
        removedKey?.includes('top_users') ||
        removedKey?.includes('users')
      
      if (keyMatches && loadTopUsersRef.current) {
        
        // Если удален другой ключ (не CACHE_KEY), также удаляем кэш компонента
        if (removedKey !== CACHE_KEY) {
          // Удаляем напрямую из localStorage, чтобы не вызвать событие
          try {
            const cacheKey = `anigo_cache_${CACHE_KEY}`
            localStorage.removeItem(cacheKey)
          } catch (err) {
            console.warn('Ошибка при удалении кэша компонента:', err)
          }
        }
        
        // Вызываем перезагрузку данных (skipCache = true, чтобы не использовать кэш)
        loadTopUsersRef.current(true)
      }
    }

    window.addEventListener('cacheRemoved', handleCacheRemoved)
    return () => {
      window.removeEventListener('cacheRemoved', handleCacheRemoved)
    }
  }, [])

  // Функция для обновления аватарки пользователя
  const updateUserAvatar = useCallback(async (username, newAvatarUrl) => {
    if (!username || !newAvatarUrl) {
      return
    }


    // Сбрасываем ошибку аватарки для этого пользователя
    setAvatarErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[username]
      return newErrors
    })

    setUsers(prevUsers => {
      // Проверяем, есть ли пользователь в списке
      const userExists = prevUsers.some(u => u.username === username)
      
      if (!userExists) {
        return prevUsers
      }
      
      const updatedUsers = prevUsers.map(user => {
        if (user.username === username) {
          // Обновляем только avatar_url, остальные данные не трогаем
          return {
            ...user,
            avatar_url: newAvatarUrl
          }
        }
        return user
      })
      usersRef.current = updatedUsers // Обновляем ref
      return updatedUsers
    })
  }, [])

  // Функция для обновления градиента пользователя
  const updateUserGradient = useCallback(async (username) => {
    if (!username) {
      return
    }


    try {
      // Получаем настройки профиля пользователя из API
      const settingsResponse = await userAPI.getUserProfileSettings(username)
      if (!settingsResponse || !settingsResponse.message) {
        return
      }

      const settings = settingsResponse.message
      
      // Получаем профиль пользователя для получения фонового изображения
      let backgroundImageUrl = null
      try {
        const profileResponse = await userAPI.getUserProfile(username)
        if (profileResponse && profileResponse.message && profileResponse.message.background_image_url) {
          backgroundImageUrl = profileResponse.message.background_image_url
        }
      } catch (err) {
        console.warn(`Не удалось получить профиль пользователя ${username} для фонового изображения:`, err)
      }
      
      setUsers(prevUsers => {
        // Проверяем, есть ли пользователь в списке
        const userExists = prevUsers.some(u => u.username === username)
        if (!userExists) {
          return prevUsers
        }
        
        // Обрабатываем данные пользователя с новыми настройками градиента
      const updatedUsers = prevUsers.map(user => {
        if (user.username === username) {
          
          // Используем настройки профиля из API
          const isPremium = settings.is_premium_profile !== undefined 
            ? settings.is_premium_profile 
            : (user.id < 100)
          
          // Если премиум включен, используем золотой цвет
          if (isPremium) {
            return {
              ...user,
              profile_settings: settings,
              background_image_url: backgroundImageUrl !== null ? backgroundImageUrl : user.background_image_url,
              accentColor: '#ffd700',
              isPremium: true,
              themeGradient: null
            }
          }
          
          // Иначе используем цвет обводки аватарки из настроек профиля
          const userColor = settings.avatar_border_color && AVAILABLE_COLORS.includes(settings.avatar_border_color)
            ? settings.avatar_border_color
            : '#e50914'
          
          // Получаем цвет никнейма из настроек профиля
          const usernameColor = settings.username_color && /^#[0-9A-Fa-f]{6}$/.test(settings.username_color)
            ? settings.username_color
            : '#ffffff' // Белый по умолчанию
          
          // Создаем градиент ТОЛЬКО из theme_color_1 и theme_color_2 из БД
          // Не используем avatar_border_color для создания градиента
          let themeGradient = null
          if (settings.theme_color_1 && settings.theme_color_2) {
            // Проверяем, что цвета валидные hex-цвета
            const color1Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_1)
            const color2Valid = /^#[0-9A-Fa-f]{6}$/.test(settings.theme_color_2)
            
            if (color1Valid && color2Valid) {
              const gradientDirection = settings.gradient_direction || 'diagonal-right'
              themeGradient = createThemeGradient(settings.theme_color_1, settings.theme_color_2, gradientDirection)
            }
          }
          
          return {
            ...user,
            profile_settings: settings,
            background_image_url: backgroundImageUrl !== null ? backgroundImageUrl : user.background_image_url,
            accentColor: userColor,
            isPremium: false,
            themeGradient: themeGradient,
            usernameColor: usernameColor
          }
        }
        return user
      })
        
        usersRef.current = updatedUsers // Обновляем ref
        return updatedUsers
      })
      
    } catch (err) {
      console.error(`Ошибка обновления градиента для ${username}:`, err)
    }
  }, [])

  // Градиенты теперь обновляются прямо в loadTopUsers при периодическом обновлении
  // Отдельная функция updateAllUsersGradients больше не нужна

  // Функция для обновления фонового изображения пользователя
  const updateUserBackgroundImage = useCallback(async (username) => {
    if (!username) {
      return
    }


    try {
      // Получаем профиль пользователя для получения фонового изображения
      const profileResponse = await userAPI.getUserProfile(username)
      if (!profileResponse || !profileResponse.message) {
        return
      }

      const profile = profileResponse.message
      const backgroundImageUrl = profile.background_image_url || null
      
      // Получаем настройки профиля для параметров отображения
      const settingsResponse = await userAPI.getUserProfileSettings(username)
      const settings = settingsResponse?.message || {}
      
      setUsers(prevUsers => {
        // Проверяем, есть ли пользователь в списке
        const userExists = prevUsers.some(u => u.username === username)
        if (!userExists) {
          return prevUsers
        }
        
        const updatedUsers = prevUsers.map(user => {
          if (user.username === username) {
            
            return {
              ...user,
              background_image_url: backgroundImageUrl,
              profile_settings: {
                ...user.profile_settings,
                ...settings
              }
            }
          }
          return user
        })
        
        usersRef.current = updatedUsers // Обновляем ref
        return updatedUsers
      })
      
    } catch (err) {
      console.error(`Ошибка обновления фонового изображения для ${username}:`, err)
    }
  }, [])

  // Обработчик обновления аватарки текущего пользователя
  useEffect(() => {
    // Функция для проверки и обновления аватарки текущего пользователя
    const checkAndUpdateAvatar = async () => {
      try {
        // Получаем текущего пользователя
        const response = await userAPI.getCurrentUser()
        if (response && response.message) {
          const user = response.message
          const username = user.username
          const avatarUrl = user.avatar_url
          
          // Проверяем, изменилась ли аватарка
          if (username && avatarUrl) {
            const prevUser = currentUserRef.current
            if (prevUser.username === username && prevUser.avatarUrl !== avatarUrl) {
              // Аватарка изменилась, обновляем только если пользователь в списке
              setUsers(prevUsers => {
                const userExists = prevUsers.some(u => u.username === username)
                if (userExists) {
                  return prevUsers.map(u => 
                    u.username === username ? { ...u, avatar_url: avatarUrl } : u
                  )
                }
                return prevUsers
              })
            }
            
            // Обновляем ref с текущими значениями
            currentUserRef.current = { username, avatarUrl }
          }
        }
      } catch (err) {
        // Игнорируем ошибки (пользователь не авторизован)
      }
    }
    
    const handleAvatarUpdate = async (event) => {
      const eventData = event?.detail
      let username = eventData?.username
      let newAvatarUrl = eventData?.avatarUrl
      
      // Если данных в событии нет, получаем их из API
      if (!username || !newAvatarUrl) {
        try {
          const response = await userAPI.getCurrentUser()
          if (response && response.message) {
            const currentUser = response.message
            username = currentUser.username
            newAvatarUrl = currentUser.avatar_url
          }
        } catch (err) {
          return
        }
      }
      
      await updateUserAvatar(username, newAvatarUrl)
      // Обновляем ref
      if (username && newAvatarUrl) {
        currentUserRef.current = { username, avatarUrl: newAvatarUrl }
      }
    }

    // Проверка localStorage для обновлений аватарки
    const checkLocalStorage = () => {
      try {
        const stored = localStorage.getItem('avatarUpdated')
        if (stored) {
          const data = JSON.parse(stored)
          if (data.timestamp && Date.now() - data.timestamp < 5 * 60 * 1000) {
            updateUserAvatar(data.username, data.avatarUrl)
            currentUserRef.current = { username: data.username, avatarUrl: data.avatarUrl }
            localStorage.removeItem('avatarUpdated')
          } else {
            localStorage.removeItem('avatarUpdated')
          }
        }
      } catch (err) {
        // Игнорируем ошибки
      }
    }

    // Проверяем localStorage при монтировании
    checkLocalStorage()
    
    // Первоначальная проверка текущего пользователя
    checkAndUpdateAvatar()

    // Периодическая проверка обновления аватарки (каждые 60 секунд)
    const interval = setInterval(() => {
      checkAndUpdateAvatar()
    }, 60000)

    // Слушаем изменения в localStorage (работает между вкладками)
    const handleStorageChange = (e) => {
      if (e.key === 'avatarUpdated' && e.newValue) {
        try {
          const data = JSON.parse(e.newValue)
          updateUserAvatar(data.username, data.avatarUrl)
          currentUserRef.current = { username: data.username, avatarUrl: data.avatarUrl }
        } catch (err) {
          // Игнорируем ошибки
        }
      }
    }

    window.addEventListener('avatarUpdated', handleAvatarUpdate)
    window.addEventListener('storage', handleStorageChange)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('avatarUpdated', handleAvatarUpdate)
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [updateUserAvatar])

  // Обработчик обновления градиента и цвета текущего пользователя
  useEffect(() => {
    const handleThemeUpdate = async () => {
      try {
        // Получаем текущего пользователя
        const response = await userAPI.getCurrentUser()
        if (response && response.message) {
          const currentUser = response.message
          const username = currentUser.username
          
          if (username) {
            // Обновляем градиент и цвет для текущего пользователя
            await updateUserGradient(username)
            // Также обновляем фоновое изображение
            await updateUserBackgroundImage(username)
          }
        }
      } catch (err) {
        // Игнорируем ошибки (пользователь не авторизован)
      }
    }

    // Обработчик обновления фонового изображения
    const handleBackgroundImageUpdate = async () => {
      try {
        // Получаем текущего пользователя
        const response = await userAPI.getCurrentUser()
        if (response && response.message) {
          const currentUser = response.message
          const username = currentUser.username
          
          if (username) {
            // Обновляем фоновое изображение для текущего пользователя
            await updateUserBackgroundImage(username)
          }
        }
      } catch (err) {
        // Игнорируем ошибки (пользователь не авторизован)
      }
    }

    // Слушаем обновления темы (градиента)
    window.addEventListener('siteThemeUpdated', handleThemeUpdate)
    // Слушаем обновления цвета обводки аватарки
    window.addEventListener('avatarBorderColorUpdated', handleThemeUpdate)
    // Слушаем обновления настроек профиля
    window.addEventListener('profileSettingsUpdated', handleThemeUpdate)
    // Слушаем обновления фонового изображения
    window.addEventListener('backgroundImageUpdated', handleBackgroundImageUpdate)
    
    return () => {
      window.removeEventListener('siteThemeUpdated', handleThemeUpdate)
      window.removeEventListener('avatarBorderColorUpdated', handleThemeUpdate)
      window.removeEventListener('profileSettingsUpdated', handleThemeUpdate)
      window.removeEventListener('backgroundImageUpdated', handleBackgroundImageUpdate)
    }
  }, [updateUserGradient, updateUserBackgroundImage])

  // Функция для преобразования hex в rgba
  const hexToRgba = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  const handleUserClick = (username) => {
    navigate(`/profile/${username}`)
  }

  // Функции для карусели
  const totalPages = Math.ceil(users.length / USERS_PER_PAGE)

  const scrollToPage = (page) => {
    if (carouselRef.current && !isScrolling) {
      setIsScrolling(true)
      const scrollAmount = page * 100
      carouselRef.current.style.transform = `translate3d(-${scrollAmount}%, 0, 0)`
      setTimeout(() => {
        setIsScrolling(false)
      }, 500)
    }
  }

  const handleNext = () => {
    if (isScrolling) return
    if (currentPage < totalPages - 1) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
      scrollToPage(nextPage)
    }
  }

  const handlePrev = () => {
    if (isScrolling) return
    if (currentPage > 0) {
      const prevPage = currentPage - 1
      setCurrentPage(prevPage)
      scrollToPage(prevPage)
    }
  }

  if (loading) {
    return (
      <section className="top-users-section anime-section">
        <div className="section-header">
          <div className="section-title-wrapper">
            <div className="sort-info-tooltip">
              <span className="tooltip-icon">?</span>
              <div className="tooltip-content">
                Пользователи отсортированы по количеству избранных аниме. Подробнее — наведите на кубок у лидера.
              </div>
            </div>
            <h2 className="section-title">Топ коллекционеров</h2>
          </div>
        </div>
        <div className="top-users-carousel-wrapper">
          <div className="top-users-carousel-container">
            {[1, 2].map((pageIndex) => (
              <div key={pageIndex} className="top-users-carousel-page">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="user-card skeleton">
                    <div className="skeleton-avatar"></div>
                    <div className="user-info">
                      <div className="skeleton-text skeleton-username"></div>
                      <div className="skeleton-text skeleton-favorites"></div>
                      <div className="user-best-anime">
                        {[1, 2, 3].map((j) => (
                          <div key={j} className="skeleton-best-anime-card"></div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="top-users-section anime-section">
        <div className="section-header">
          <div className="section-title-wrapper">
            <div className="sort-info-tooltip">
              <span className="tooltip-icon">?</span>
              <div className="tooltip-content">
                Пользователи отсортированы по количеству избранных аниме. Подробнее — наведите на кубок у лидера.
              </div>
            </div>
            <h2 className="section-title">Топ коллекционеров</h2>
          </div>
        </div>
        <div className="error-message">{error}</div>
      </section>
    )
  }

  if (users.length === 0) {
    return null
  }

  const shouldShowControls = users.length > USERS_PER_PAGE
  const shouldShowIndicators = totalPages > 1

  return (
    <>
      {tooltipPosition.visible && createPortal(
        <div 
          ref={tooltipRef}
          className="trophy-tooltip-content"
          style={{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`,
            position: 'fixed',
            zIndex: 99999
          }}
          onMouseEnter={() => setTooltipPosition(prev => ({ ...prev, visible: true }))}
          onMouseLeave={() => setTooltipPosition(prev => ({ ...prev, visible: false }))}
        >
          Пользователь, занявший первое место по итогам недели, получит эксклюзивный бейдж «<span className="trophy-tooltip-gold-text">Коллекционер #1</span>» — он будет отображаться только у вас в профиле на всю следующую неделю
          <div className="trophy-tooltip-divider"></div>
          <div className="trophy-tooltip-secondary-text">Данные обновляются каждые 15 минут</div>
        </div>,
        document.body
      )}
      <section className="top-users-section anime-section">
        <div className="section-header">
          <div className="section-title-wrapper">
            <div className="sort-info-tooltip">
              <span className="tooltip-icon">?</span>
              <div className="tooltip-content">
                Пользователи отсортированы по количеству избранных аниме. Подробнее — наведите на кубок у лидера.
              </div>
            </div>
            <h2 className="section-title">Топ коллекционеров</h2>
          </div>
        {shouldShowControls && (
          <div className="carousel-controls">
            <button 
              className="carousel-btn prev" 
              onClick={handlePrev}
              disabled={currentPage === 0 || isScrolling}
              aria-label="Предыдущая страница"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
            </button>
            <button 
              className="carousel-btn next" 
              onClick={handleNext}
              disabled={currentPage >= totalPages - 1 || isScrolling}
              aria-label="Следующая страница"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        )}
      </div>
      <div className="top-users-carousel-wrapper">
        <div className="top-users-carousel-container" ref={carouselRef}>
          {Array.from({ length: totalPages }, (_, pageIndex) => {
            const startIndex = pageIndex * USERS_PER_PAGE
            const endIndex = startIndex + USERS_PER_PAGE
            const pageUsers = users.slice(startIndex, endIndex)
            
            return (
              <div key={pageIndex} className="top-users-carousel-page">
                {pageUsers.map((user, userIndex) => {
                  const globalIndex = startIndex + userIndex
                  const userColor = user.accentColor || '#e50914'
                  const isPremium = user.isPremium || false
                  const themeGradient = user.themeGradient || null
                  
                  // Получаем фоновое изображение и параметры отображения
                  const backgroundImageUrl = user.background_image_url || null
                  const settings = user.profile_settings || {}
                  const backgroundScale = settings.background_scale || 100
                  const backgroundPositionX = settings.background_position_x || 50
                  const backgroundPositionY = settings.background_position_y || 50
                  const hasBackgroundImageError = backgroundImageErrors[user.username] || false
                  
                  // Для премиум используем специальное золотое свечение
                  let rgbaColor, rgbaColorLight
                  if (isPremium) {
                    rgbaColor = 'rgba(255, 215, 0, 0.4)'
                    rgbaColorLight = 'rgba(255, 215, 0, 0.3)'
                  } else {
                    rgbaColor = hexToRgba(userColor, 0.4) // 0.4 для соответствия профилю
                    rgbaColorLight = hexToRgba(userColor, 0.2)
                  }
                  
                  // Определяем стили для карточки
                  let cardStyle = {}
                  if (isPremium) {
                    cardStyle = {
                      '--user-glow-color': userColor,
                      '--user-glow-rgba': rgbaColor,
                      '--user-glow-rgba-light': rgbaColorLight
                    }
                  } else {
                    cardStyle = {
                      '--user-glow-color': userColor,
                      '--user-glow-rgba': rgbaColor,
                      '--user-glow-rgba-light': rgbaColorLight,
                      border: `1px solid ${userColor}`
                    }
                    // Если есть градиент, применяем его к фону
                    if (themeGradient) {
                      // Используем CSS переменную для градиента (как в профиле)
                      cardStyle['--user-theme-gradient'] = themeGradient
                      // Также устанавливаем background напрямую для надежности
                      cardStyle.background = themeGradient
                      cardStyle.backgroundImage = themeGradient
                      cardStyle.backgroundColor = 'transparent'
                    }
                  }
                  
                  // Применяем фоновое изображение к карточке, если оно есть
                  if (backgroundImageUrl && !hasBackgroundImageError) {
                    cardStyle['--card-bg-image'] = `url("${backgroundImageUrl}")`
                    // Используем cover для заполнения всей карточки без черных полос
                    cardStyle['--card-bg-size'] = 'cover'
                    cardStyle['--card-bg-position'] = `${backgroundPositionX}% ${backgroundPositionY}%`
                    cardStyle['--card-bg-opacity'] = '1'
                  } else {
                    cardStyle['--card-bg-image'] = 'none'
                    cardStyle['--card-bg-opacity'] = '0'
                  }
                  
                  return (
                    <div 
                      key={user.username} 
                      className={`user-card ${isPremium ? 'premium-card' : ''} ${themeGradient ? 'has-gradient' : ''}`}
                      onClick={() => handleUserClick(user.username)}
                      style={cardStyle}
                    >
                      {/* Скрытый img для проверки загрузки фонового изображения карточки */}
                      {backgroundImageUrl && !hasBackgroundImageError && (
                        <img
                          src={backgroundImageUrl}
                          alt=""
                          style={{
                            position: 'absolute',
                            width: 0,
                            height: 0,
                            opacity: 0,
                            pointerEvents: 'none',
                            zIndex: -1
                          }}
                          onError={() => {
                            console.warn(`⚠️ Ошибка загрузки фонового изображения для ${user.username}:`, backgroundImageUrl)
                            setBackgroundImageErrors(prev => ({
                              ...prev,
                              [user.username]: true
                            }))
                          }}
                          onLoad={() => {
                            // Изображение загружено успешно, сбрасываем ошибку если была
                            setBackgroundImageErrors(prev => {
                              const newErrors = { ...prev }
                              delete newErrors[user.username]
                              return newErrors
                            })
                          }}
                        />
                      )}
                      <div 
                        className={`user-avatar-wrapper ${isPremium ? 'premium-avatar-wrapper' : ''}`}
                        style={{
                          '--user-glow-color': userColor,
                          '--user-glow-rgba': rgbaColor,
                          '--user-glow-rgba-light': rgbaColorLight
                        }}
                      >
                        {globalIndex === 0 ? (
                          <div 
                            ref={trophyRef}
                            className="trophy-tooltip"
                            onMouseEnter={(e) => {
                              if (trophyRef.current) {
                                const rect = trophyRef.current.getBoundingClientRect()
                                const tooltipWidth = 350 // Примерная ширина tooltip
                                const offset = 15
                                
                                // Позиционируем tooltip слева или справа от кубка
                                let left = rect.right + offset
                                let top = rect.top
                                
                                // Проверяем, не выходит ли tooltip за правую границу экрана
                                if (left + tooltipWidth > window.innerWidth) {
                                  left = rect.left - tooltipWidth - offset
                                }
                                
                                // Проверяем, не выходит ли tooltip за верхнюю границу
                                if (top < 0) {
                                  top = offset
                                }
                                
                                setTooltipPosition({
                                  x: left,
                                  y: top,
                                  visible: true
                                })
                              }
                            }}
                            onMouseLeave={() => setTooltipPosition(prev => ({ ...prev, visible: false }))}
                          >
                            <div className={`user-rank first-place`}>
                              <img 
                                src="/main_kubok.png"
                                alt="Кубок"
                                className="trophy-icon"
                              />
                            </div>
                          </div>
                        ) : (
                          <div className={`user-rank`}>
                            {globalIndex + 1}
                          </div>
                        )}
                        {(() => {
                          const avatarUrl = normalizeAvatarUrl(user.avatar_url)
                          const hasAvatarError = avatarErrors[user.username] || false
                          
                          // Показываем изображение только если есть валидный нормализованный URL и нет ошибки загрузки
                          if (avatarUrl && typeof avatarUrl === 'string' && avatarUrl.length > 0 && !hasAvatarError) {
                            return (
                              <img 
                                key={`${user.username}-${user.avatar_url || 'no-avatar'}`}
                                src={avatarUrl} 
                                alt={user.username}
                                className="user-avatar"
                                style={{
                                  border: isPremium ? 'none' : `4px solid ${userColor}`,
                                  boxShadow: isPremium ? 'none' : `0 4px 12px ${rgbaColor}, 0 0 16px ${rgbaColorLight}`
                                }}
                                onError={(e) => {
                                  // Останавливаем повторные попытки загрузки
                                  e.target.src = ''
                                  // При ошибке загрузки сохраняем ошибку в состоянии
                                  setAvatarErrors(prev => ({
                                    ...prev,
                                    [user.username]: true
                                  }))
                                }}
                                onLoad={() => {
                                  // При успешной загрузке сбрасываем ошибку
                                  setAvatarErrors(prev => {
                                    const newErrors = { ...prev }
                                    delete newErrors[user.username]
                                    return newErrors
                                  })
                                }}
                              />
                            )
                          } else {
                            // Показываем fallback с инициалами если нет аватарки или произошла ошибка загрузки
                            return (
                              <div 
                                className="user-avatar-initials"
                                style={{ 
                                  backgroundColor: getColorFromUsername(user.username),
                                  border: isPremium ? 'none' : `4px solid ${userColor}`,
                                  boxShadow: isPremium ? 'none' : `0 4px 12px ${rgbaColor}, 0 0 16px ${rgbaColorLight}`
                                }}
                              >
                                {getInitials(user.username)}
                              </div>
                            )
                          }
                        })()}
                      </div>
                      <div className="user-info">
                        <div 
                          className={`user-name ${isPremium ? 'premium-user-name' : ''}`}
                          style={!isPremium && user.usernameColor && user.usernameColor !== 'premium' ? { color: user.usernameColor } : undefined}
                        >
                          <span className="user-name-text">{user.username}</span>
                          {(isPremium || user.type_account === 'admin' || user.type_account === 'owner') && (
                            <span className="crown-icon-top-users">
                              <CrownIcon size={18} />
                            </span>
                          )}
                        </div>
                        <div className="user-stats">
                          <span 
                            className={`favorites-count ${isPremium ? 'premium-favorites' : ''}`}
                            style={!isPremium && user.usernameColor && user.usernameColor !== 'premium' ? { color: user.usernameColor } : undefined}
                          >
                            <svg 
                              width="16" 
                              height="16" 
                              viewBox="0 0 24 24" 
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              className={`favorites-heart-icon ${isPremium ? 'premium-heart-icon' : ''}`}
                              style={!isPremium && user.usernameColor && user.usernameColor !== 'premium' ? { color: user.usernameColor } : undefined}
                            >
                              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                            </svg>
                            {user.amount}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
      {shouldShowIndicators && (
        <div className="carousel-indicators">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              className={`indicator ${i === currentPage ? 'active' : ''}`}
              onClick={() => {
                if (isScrolling) return
                setCurrentPage(i)
                scrollToPage(i)
              }}
              aria-label={`Страница ${i + 1}`}
            />
          ))}
        </div>
      )}
    </section>
    </>
  )
})

export default TopUsersSection

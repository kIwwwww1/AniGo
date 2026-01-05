import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { userAPI } from './services/api'
import HomePage from './pages/HomePage'
import WatchPage from './pages/WatchPage'
import WatchPageSearch from './pages/WatchPageSearch'
import MyFavoritesPage from './pages/MyFavoritesPage'
import UserProfilePage from './pages/UserProfilePage'
import SettingsPage from './pages/SettingsPage'
import PopularAnimePage from './pages/PopularAnimePage'
import AllAnimePage from './pages/AllAnimePage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import Layout from './components/Layout'
import ScrollToTop from './components/ScrollToTop'
import PageTransition from './components/PageTransition'
import './components/PageTransition.css'

// Функция для обновления глобального цвета кнопок
const updateGlobalAccentColor = (color) => {
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
  
  const rgbaColor = (hex, alpha) => {
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
  // Низкая оценка (1-3) - приглушенный цвет
  const lowColor = darkenColor(color, 0.3)
  const lowColorLight = lightenColor(lowColor, 0.2)
  document.documentElement.style.setProperty('--user-accent-color-low', lowColor)
  document.documentElement.style.setProperty('--user-accent-color-low-light', lowColorLight)
  document.documentElement.style.setProperty('--user-accent-color-border-low', rgbaColor(color, 0.4))
  document.documentElement.style.setProperty('--user-accent-color-shadow-low', rgbaColor(color, 0.3))
  
  // Средняя оценка (4-6) - средний цвет
  const mediumColor = color
  const mediumColorLight = lightenColor(color, 0.15)
  document.documentElement.style.setProperty('--user-accent-color-medium', mediumColor)
  document.documentElement.style.setProperty('--user-accent-color-medium-light', mediumColorLight)
  document.documentElement.style.setProperty('--user-accent-color-border-medium', rgbaColor(color, 0.5))
  document.documentElement.style.setProperty('--user-accent-color-shadow-medium', rgbaColor(color, 0.4))
  
  // Высокая оценка (7-9) - яркий цвет
  const highColor = lightenColor(color, 0.2)
  const highColorLight = lightenColor(color, 0.35)
  document.documentElement.style.setProperty('--user-accent-color-high', highColor)
  document.documentElement.style.setProperty('--user-accent-color-high-light', highColorLight)
  document.documentElement.style.setProperty('--user-accent-color-border-high', rgbaColor(color, 0.6))
  document.documentElement.style.setProperty('--user-accent-color-shadow-high', rgbaColor(color, 0.5))
  
  // Идеальная оценка (10) - максимально яркий цвет
  const perfectColor = lightenColor(color, 0.4)
  document.documentElement.style.setProperty('--user-accent-color-perfect', perfectColor)
  document.documentElement.style.setProperty('--user-accent-color-shadow-perfect', rgbaColor(color, 0.6))
  document.documentElement.style.setProperty('--user-accent-color-shadow-perfect-light', rgbaColor(color, 0.3))
  
  // Общие переменные для границ
  document.documentElement.style.setProperty('--user-accent-color-border', rgbaColor(color, 0.3))
  
  // Темный фон для идеальной оценки
  const bgDark = `rgba(${Math.floor(r * 0.08)}, ${Math.floor(g * 0.08)}, ${Math.floor(b * 0.08)}, 0.95)`
  document.documentElement.style.setProperty('--user-accent-color-bg-dark', bgDark)
}

// Функция для загрузки цвета обводки аватарки текущего пользователя
const loadUserAccentColor = async () => {
  try {
    const response = await userAPI.getCurrentUser()
    if (response.message && response.message.username) {
      const username = response.message.username
      const savedAvatarBorderColor = localStorage.getItem(`user_${username}_avatar_border_color`)
      
      // Доступные цвета
      const availableColors = [
        '#ffffff', '#000000', '#808080', '#c4c4af', 
        '#0066ff', '#00cc00', '#ff0000', '#ff69b4', 
        '#ffd700', '#9932cc'
      ]
      
      if (savedAvatarBorderColor && availableColors.includes(savedAvatarBorderColor)) {
        updateGlobalAccentColor(savedAvatarBorderColor)
      } else {
        // Используем цвет по умолчанию
        updateGlobalAccentColor('#ff0000')
      }
    }
  } catch (err) {
    // Если пользователь не авторизован, используем цвет по умолчанию
    updateGlobalAccentColor('#e50914')
  }
}

// Функция для загрузки темы (теперь только для темной темы по умолчанию)
export const loadTheme = () => {
  const savedThemeColor = localStorage.getItem('site-theme-color')
  if (!savedThemeColor) {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
  // Кастомная тема загружается через UserProfilePage
}

function App() {
  useEffect(() => {
    // Загружаем кастомную тему при загрузке приложения
    const savedThemeColor1 = localStorage.getItem('site-theme-color-1')
    const savedThemeColor2 = localStorage.getItem('site-theme-color-2')
    const savedGradientDirection = localStorage.getItem('site-gradient-direction') || 'diagonal-right'
    
    if (savedThemeColor1 && savedThemeColor2) {
      // Используем глобальную функцию из UserProfilePage
      if (window.applyCustomTheme) {
        window.applyCustomTheme(savedThemeColor1, savedThemeColor2, savedGradientDirection)
      } else {
        // Если функция еще не загружена, устанавливаем темную тему
        document.documentElement.setAttribute('data-theme', 'dark')
      }
    } else {
      document.documentElement.setAttribute('data-theme', 'dark')
    }
    
    // Загружаем цвет при загрузке приложения
    loadUserAccentColor()
    
    // Слушаем изменения в localStorage для обновления цвета (работает между вкладками)
    const handleStorageChange = (e) => {
      if (e.key && e.key.startsWith('user_') && e.key.endsWith('_avatar_border_color')) {
        loadUserAccentColor()
      } else if (e.key === 'site-theme-color-1' || e.key === 'site-theme-color-2' || e.key === 'site-gradient-direction') {
        const savedThemeColor1 = localStorage.getItem('site-theme-color-1')
        const savedThemeColor2 = localStorage.getItem('site-theme-color-2')
        const savedGradientDirection = localStorage.getItem('site-gradient-direction') || 'diagonal-right'
        if (savedThemeColor1 && savedThemeColor2 && window.applyCustomTheme) {
          window.applyCustomTheme(savedThemeColor1, savedThemeColor2, savedGradientDirection)
        } else {
          document.documentElement.setAttribute('data-theme', 'dark')
        }
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    
    // Для обновления в текущей вкладке используем кастомное событие
    const handleColorUpdate = () => {
      loadUserAccentColor()
    }
    
    window.addEventListener('userAccentColorUpdated', handleColorUpdate)
    
    // Слушаем изменения темы (кастомная тема обрабатывается в UserProfilePage)
    const handleThemeUpdate = () => {
      // Кастомная тема обрабатывается в UserProfilePage через applyCustomTheme
      // Здесь просто проверяем, нужно ли сбросить на темную
      const savedThemeColor = localStorage.getItem('site-theme-color')
      if (!savedThemeColor) {
        document.documentElement.setAttribute('data-theme', 'dark')
      }
    }
    
    window.addEventListener('siteThemeUpdated', handleThemeUpdate)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('userAccentColorUpdated', handleColorUpdate)
      window.removeEventListener('siteThemeUpdated', handleThemeUpdate)
    }
  }, [])

  return (
    <Router>
      <ScrollToTop />
      <PageTransition>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/my" element={<MyFavoritesPage />} />
            <Route path="/watch/:animeId" element={<WatchPage />} />
            <Route path="/watch/search/:animeName" element={<WatchPageSearch />} />
            <Route path="/profile/:username" element={<UserProfilePage />} />
            <Route path="/settings/:username" element={<SettingsPage />} />
            <Route path="/anime/all/popular" element={<PopularAnimePage />} />
            <Route path="/anime/all/anime" element={<AllAnimePage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
          </Routes>
        </Layout>
      </PageTransition>
    </Router>
  )
}

export default App


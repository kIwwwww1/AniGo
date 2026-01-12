import { useState, useEffect, useRef } from 'react'
import './LoadingScreen.css'

function LoadingScreen({ isLoading }) {
  const [visible, setVisible] = useState(true)
  const timeoutRef = useRef(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    
    // Очищаем предыдущий таймер
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }

    if (isLoading) {
      // Показываем экран
      setVisible(true)
    } else {
      // Скрываем экран через небольшую задержку для fade out
      timeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          setVisible(false)
        }
      }, 400) // Время для плавного fade out
    }

    // Резервный таймер - гарантированно скрываем через 4 секунды
    const safetyTimer = setTimeout(() => {
      if (mountedRef.current) {
        setVisible(false)
      }
    }, 4000)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      clearTimeout(safetyTimer)
    }
  }, [isLoading])

  // Не рендерим если не видим
  if (!visible && !isLoading) {
    return null
  }

  return (
    <div 
      className={`loading-screen ${!isLoading && visible ? 'fading-out' : ''}`}
      style={!visible && !isLoading ? { display: 'none' } : {}}
    >
      <div className="loading-screen-content">
        <div className="loading-logo">
          <h1>Yumivo</h1>
        </div>
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
      </div>
    </div>
  )
}

export default LoadingScreen

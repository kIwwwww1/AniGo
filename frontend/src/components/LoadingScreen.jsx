import { useState, useEffect, useRef } from 'react'
import './LoadingScreen.css'

function LoadingScreen({ isLoading, onComplete }) {
  const [shouldShow, setShouldShow] = useState(true)
  const fadeTimeoutRef = useRef(null)
  const prevLoadingRef = useRef(isLoading)

  useEffect(() => {
    // Очищаем предыдущий таймер если есть
    if (fadeTimeoutRef.current) {
      clearTimeout(fadeTimeoutRef.current)
      fadeTimeoutRef.current = null
    }

    if (isLoading) {
      // Если начинается загрузка, сразу показываем экран
      setShouldShow(true)
      prevLoadingRef.current = true
    } else if (!isLoading && prevLoadingRef.current) {
      // Если загрузка закончилась и мы были в состоянии загрузки, начинаем fade out
      prevLoadingRef.current = false
      fadeTimeoutRef.current = setTimeout(() => {
        setShouldShow(false)
        if (onComplete) {
          onComplete()
        }
      }, 1000) // Время анимации рассеивания
    }

    return () => {
      if (fadeTimeoutRef.current) {
        clearTimeout(fadeTimeoutRef.current)
      }
    }
  }, [isLoading, onComplete])

  // Не рендерим если не нужно показывать
  if (!shouldShow && !isLoading) {
    return null
  }

  return (
    <div className={`loading-screen ${!isLoading && shouldShow ? 'fading-out' : ''}`}>
      <div className="loading-screen-content">
        <div className="loading-logo">
          <h1>AniGo</h1>
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


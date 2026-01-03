import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import LoadingScreen from './LoadingScreen'

function PageTransition({ children }) {
  const location = useLocation()
  const [isLoading, setIsLoading] = useState(true)
  const [isFirstLoad, setIsFirstLoad] = useState(true)
  const prevLocationRef = useRef(location.pathname)
  const loadingTimeoutRef = useRef(null)

  useEffect(() => {
    // Очищаем предыдущий таймер если есть
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current)
      loadingTimeoutRef.current = null
    }

    // При изменении маршрута сразу показываем экран загрузки
    if (location.pathname !== prevLocationRef.current) {
      setIsLoading(true)
      prevLocationRef.current = location.pathname
      setIsFirstLoad(false)
    }
    
    // Скрываем экран загрузки через минимальное время для плавности
    loadingTimeoutRef.current = setTimeout(() => {
      setIsLoading(false)
    }, isFirstLoad ? 1200 : 1000) // Больше времени при первой загрузке
    
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current)
      }
    }
  }, [location.pathname, isFirstLoad])

  const handleLoadingComplete = () => {
    // Callback вызывается после завершения анимации fade out
  }

  return (
    <>
      <LoadingScreen 
        isLoading={isLoading} 
        onComplete={handleLoadingComplete}
      />
      <div className={`page-content ${isLoading ? 'loading' : 'loaded'}`}>
        {children}
      </div>
    </>
  )
}

export default PageTransition


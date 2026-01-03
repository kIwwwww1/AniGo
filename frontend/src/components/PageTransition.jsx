import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import LoadingScreen from './LoadingScreen'

function PageTransition({ children }) {
  const location = useLocation()
  const [isLoading, setIsLoading] = useState(false)
  const prevLocationRef = useRef(location.pathname)
  const timeoutRef = useRef(null)
  const isInitialMountRef = useRef(true)

  useEffect(() => {
    // Очищаем предыдущий таймер
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }

    // При первой загрузке показываем экран загрузки только если мы на главной странице
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false
      // Показываем экран загрузки только на главной странице
      if (location.pathname === '/') {
        setIsLoading(true)
        // Гарантированно скрываем через 1.5 секунды
        timeoutRef.current = setTimeout(() => {
          setIsLoading(false)
        }, 1500)
      } else {
        // Если не на главной, сразу скрываем
        setIsLoading(false)
      }
      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
      }
    }

    // При изменении маршрута не показываем экран загрузки
    if (location.pathname !== prevLocationRef.current) {
      prevLocationRef.current = location.pathname
      // Убеждаемся что экран загрузки скрыт
      setIsLoading(false)
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [location.pathname])

  // Резервный таймер - гарантированно скрываем через 2 секунды если isLoading = true
  useEffect(() => {
    if (isLoading) {
      const safetyTimer = setTimeout(() => {
        setIsLoading(false)
      }, 2000)

      return () => {
        clearTimeout(safetyTimer)
      }
    }
  }, [isLoading])

  // Гарантируем, что контент всегда виден, если не идет загрузка
  const shouldShowContent = !isLoading

  return (
    <>
      <LoadingScreen isLoading={isLoading} />
      <div 
        className={`page-content ${isLoading ? 'loading' : 'loaded'}`}
        style={shouldShowContent ? { 
          opacity: 1, 
          visibility: 'visible', 
          pointerEvents: 'auto' 
        } : {}}
      >
        {children}
      </div>
    </>
  )
}

export default PageTransition

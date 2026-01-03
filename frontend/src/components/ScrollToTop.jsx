import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    // Прокручиваем страницу в самый верх при изменении маршрута
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'instant' // Мгновенная прокрутка без анимации
    })
  }, [pathname])

  return null
}

export default ScrollToTop


import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './AnimeCardGrid.css'

function AnimeGrid({ 
  title, 
  animeList = [], 
  itemsPerPage = 6, 
  maxPagesToShow = 3,
  showExpandButton = false,
  showControls = true,
  showIndicators = true,
  emptyMessage = 'Нет аниме для отображения',
  totalCount = null, // Общее количество элементов (если известно)
  onExpand,
  onPageChange,
  className = ''
}) {
  const [currentPage, setCurrentPage] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const carouselRef = useRef(null)

  // Сбрасываем страницу при изменении списка
  useEffect(() => {
    if (carouselRef.current) {
      setCurrentPage(0)
      carouselRef.current.style.transform = 'translate3d(0%, 0, 0)'
    }
  }, [animeList.length])

  // Определяем класс оценки в зависимости от значения
  const getScoreClass = (scoreValue) => {
    if (!scoreValue) return ''
    const score = parseFloat(scoreValue)
    if (score === 10) return 'score-perfect'
    if (score >= 7 && score < 10) return 'score-high'
    if (score >= 4 && score < 7) return 'score-medium'
    if (score >= 1 && score < 4) return 'score-low'
    return ''
  }

  const handleNext = () => {
    const totalPages = Math.ceil(animeList.length / itemsPerPage)
    const maxPages = showAll ? totalPages : Math.min(maxPagesToShow, totalPages)
    if (currentPage < maxPages - 1) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
      scrollToPage(nextPage)
      if (onPageChange) {
        onPageChange(nextPage, nextPage * itemsPerPage)
      }
    }
  }

  const handlePrev = () => {
    if (currentPage > 0) {
      const prevPage = currentPage - 1
      setCurrentPage(prevPage)
      scrollToPage(prevPage)
      if (onPageChange) {
        onPageChange(prevPage, prevPage * itemsPerPage)
      }
    }
  }

  const scrollToPage = (page) => {
    if (carouselRef.current) {
      const scrollAmount = page * 100
      carouselRef.current.style.transform = `translate3d(-${scrollAmount}%, 0, 0)`
    }
  }

  const handleExpand = async () => {
    setShowAll(true)
    if (onExpand) {
      await onExpand()
    }
  }

  // Используем totalCount, если он передан, иначе используем длину списка
  const effectiveTotal = totalCount !== null && totalCount > 0 ? totalCount : animeList.length
  const totalPages = Math.ceil(effectiveTotal / itemsPerPage)
  const displayPages = showAll ? totalPages : Math.min(maxPagesToShow, totalPages)
  const hasMore = totalPages > maxPagesToShow && !showAll
  
  // Упрощенная логика: показываем контролы всегда, если есть элементы и включены контролы
  // Временно упрощаем - показываем контролы всегда, если есть элементы (для отладки)
  const shouldShowControls = showControls && animeList.length > 0
  const shouldShowIndicators = showIndicators && animeList.length > 0 && displayPages > 1

  if (animeList.length === 0) {
    return (
      <section className={`anime-card-grid-section ${className}`}>
        <div className="section-header">
          {title && (
            <div className="section-title-wrapper">
              <h2 className="section-title">{title}</h2>
            </div>
          )}
        </div>
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
          {emptyMessage}
        </div>
      </section>
    )
  }

  return (
    <section className={`anime-card-grid-section ${className}`}>
      <div className="section-header">
        {title && (
          <div className="section-title-wrapper">
            <h2 className="section-title">{title}</h2>
            {showExpandButton && (
              <button 
                className="section-expand-btn"
                onClick={handleExpand}
                aria-label="Показать все аниме"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            )}
          </div>
        )}
        {shouldShowControls ? (
          <div className="carousel-controls">
            <button 
              className="carousel-btn prev" 
              onClick={handlePrev}
              disabled={currentPage === 0}
              aria-label="Предыдущая страница"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
            </button>
            <button 
              className="carousel-btn next" 
              onClick={handleNext}
              disabled={currentPage >= displayPages - 1}
              aria-label="Следующая страница"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        ) : null}
      </div>

      <div className="anime-card-grid-wrapper">
        <div className="anime-card-grid-container" ref={carouselRef}>
          {Array.from({ length: displayPages }, (_, pageIndex) => (
            <div key={pageIndex} className="anime-card-grid-page">
              {animeList.slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage).map((anime) => {
                const score = anime.score ? parseFloat(anime.score) : null
                const scoreClass = getScoreClass(score)
                const scoreDisplay = score ? score.toFixed(1) : null

                return (
                  <div key={anime.id} className="anime-card-grid-item">
                    <Link
                      to={`/watch/${anime.id}`}
                      className="anime-card-grid-card"
                    >
                      <div className="anime-card-poster">
                        <img 
                          src={anime.poster_url || '/placeholder.jpg'} 
                          alt={anime.title}
                          loading="lazy"
                        />
                        {score && (
                          <div className={`anime-card-score ${scoreClass}`}>
                            {score === 10 ? <span className="star-icon">🌟</span> : <span>★</span>}
                            {scoreDisplay}
                          </div>
                        )}
                      </div>
                    </Link>
                    <div className="anime-card-title">{anime.title || 'Без названия'}</div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {shouldShowIndicators && (
        <div className="carousel-indicators">
          {Array.from({ length: displayPages }, (_, i) => (
            <button
              key={i}
              className={`indicator ${i === currentPage ? 'active' : ''}`}
              onClick={() => {
                setCurrentPage(i)
                scrollToPage(i)
                if (onPageChange) {
                  onPageChange(i, i * itemsPerPage)
                }
              }}
              aria-label={`Страница ${i + 1}`}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default AnimeGrid


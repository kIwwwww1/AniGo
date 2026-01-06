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
  className = '',
  sortCriteria = null // Описание критерия сортировки для tooltip
}) {
  const [currentPage, setCurrentPage] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const [isScrolling, setIsScrolling] = useState(false)
  const carouselRef = useRef(null)
  const prevListLengthRef = useRef(animeList.length)

  // Сбрасываем страницу только если список полностью изменился (не просто добавились элементы)
  useEffect(() => {
    // Сбрасываем только если список стал короче или полностью изменился
    if (animeList.length < prevListLengthRef.current) {
      if (carouselRef.current) {
        setCurrentPage(0)
        carouselRef.current.style.transform = 'translate3d(0%, 0, 0)'
      }
    }
    prevListLengthRef.current = animeList.length
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

  // Вычисляем значения страниц один раз
  const effectiveTotal = totalCount !== null && totalCount > 0 ? totalCount : animeList.length
  const totalPages = Math.ceil(effectiveTotal / itemsPerPage)
  const displayPages = showAll ? totalPages : Math.min(maxPagesToShow, totalPages)

  const scrollToPage = (page) => {
    if (carouselRef.current && !isScrolling) {
      setIsScrolling(true)
      const scrollAmount = page * 100
      carouselRef.current.style.transform = `translate3d(-${scrollAmount}%, 0, 0)`
      // Сбрасываем флаг после завершения анимации
      setTimeout(() => {
        setIsScrolling(false)
      }, 500) // Время анимации из CSS
    }
  }

  const handleNext = () => {
    if (isScrolling) return // Предотвращаем двойные клики
    
    // Проверяем, что есть следующая страница
    if (currentPage < displayPages - 1) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
      scrollToPage(nextPage)
      if (onPageChange) {
        onPageChange(nextPage, nextPage * itemsPerPage)
      }
    }
  }

  const handlePrev = () => {
    if (isScrolling) return // Предотвращаем двойные клики
    
    if (currentPage > 0) {
      const prevPage = currentPage - 1
      setCurrentPage(prevPage)
      scrollToPage(prevPage)
      if (onPageChange) {
        onPageChange(prevPage, prevPage * itemsPerPage)
      }
    }
  }

  const handleExpand = async () => {
    setShowAll(true)
    if (onExpand) {
      await onExpand()
    }
  }

  // hasMore вычисляется на основе уже вычисленных значений
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
            {sortCriteria && (
              <div className="sort-info-tooltip">
                <span className="tooltip-icon">?</span>
                <div className="tooltip-content">
                  {sortCriteria}
                </div>
              </div>
            )}
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
            {sortCriteria && (
              <div className="sort-info-tooltip">
                <span className="tooltip-icon">?</span>
                <div className="tooltip-content">
                  {sortCriteria}
                </div>
              </div>
            )}
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
              disabled={currentPage >= displayPages - 1 || isScrolling}
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
          {Array.from({ length: displayPages }, (_, pageIndex) => {
            const startIndex = pageIndex * itemsPerPage
            const endIndex = (pageIndex + 1) * itemsPerPage
            
            // Определяем, нужно ли заполнять пустые места skeleton
            // Заполняем если totalCount больше чем реальных аниме (значит ожидается больше аниме)
            const hasMoreExpected = totalCount !== null && totalCount > 0 && totalCount > animeList.length
            
            // Создаем массив элементов для страницы (всегда itemsPerPage элементов)
            const pageItems = Array.from({ length: itemsPerPage }, (_, itemIndex) => {
              const globalIndex = startIndex + itemIndex
              
              // Если есть реальное аниме на этой позиции
              if (globalIndex < animeList.length) {
                return animeList[globalIndex]
              }
              
              // Если ожидается больше аниме и позиция в пределах ожидаемого totalCount
              if (hasMoreExpected && globalIndex < totalCount) {
                return {
                  id: `skeleton-${pageIndex}-${itemIndex}`,
                  isSkeleton: true,
                  isPlaceholder: true
                }
              }
              
              // Если не ожидается больше аниме, не показываем элемент (страница будет неполной)
              return null
            }).filter(item => item !== null)
            
            return (
              <div key={pageIndex} className="anime-card-grid-page">
                {pageItems.map((anime, itemIndex) => {
                  const isSkeleton = anime.isPlaceholder === true || anime.isSkeleton === true || (!anime.poster_url && !anime.title && anime.id?.startsWith('skeleton-'))
                  const score = anime.score ? parseFloat(anime.score) : null
                  const scoreClass = getScoreClass(score)
                  const scoreDisplay = score ? score.toFixed(1) : null

                  if (isSkeleton) {
                    return (
                      <div key={anime.id || `skeleton-${pageIndex}-${itemIndex}`} className="anime-card-grid-item">
                        <div className="anime-card-grid-card skeleton-card">
                          <div className="anime-card-poster skeleton-poster">
                            <div className="skeleton-shimmer"></div>
                          </div>
                        </div>
                        <div className="anime-card-title skeleton-title">
                          <div className="skeleton-shimmer"></div>
                        </div>
                      </div>
                    )
                  }

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
            )
          })}
        </div>
      </div>

      {shouldShowIndicators && (
        <div className="carousel-indicators">
          {Array.from({ length: displayPages }, (_, i) => (
            <button
              key={i}
              className={`indicator ${i === currentPage ? 'active' : ''}`}
              onClick={() => {
                if (isScrolling) return // Предотвращаем клики во время прокрутки
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


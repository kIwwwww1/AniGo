import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { animeAPI } from '../services/api'
import './PopularAnimeCarousel.css'

function PopularAnimeCarousel() {
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const carouselRef = useRef(null)
  const itemsPerPage = 6
  const maxPagesToShow = 3

  // Функция для создания пустых карточек
  const createEmptyCards = (count) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `empty-${i}`,
      title: 'Не определено',
      poster_url: null,
      score: null,
      isPlaceholder: true
    }))
  }

  useEffect(() => {
    loadAnimeCount()
    loadAnime(0)
  }, [])

  const loadAnimeCount = async () => {
    try {
      const response = await animeAPI.getAnimeCount()
      const count = response.message || 0
      setTotalCount(count)
    } catch (err) {
      console.error('Ошибка загрузки количества популярных аниме:', err)
      setTotalCount(0)
    }
  }

  const loadAnime = async (offset) => {
    try {
      setLoading(true)
      setHasError(false)
      
      console.log(`Загрузка популярных аниме: limit=${itemsPerPage}, offset=${offset}`)
      
      const response = await animeAPI.getPopularAnime(itemsPerPage, offset)
      
      console.log('Ответ от API:', response)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      console.log(`Получено аниме: ${animeData.length}`)
      
      if (animeData.length > 0) {
        if (offset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === itemsPerPage)
      } else {
        // Если данных нет, показываем пустые карточки
        console.log('Данных нет, показываем пустые карточки')
        if (offset === 0) {
          setAnimeList(createEmptyCards(itemsPerPage))
        }
        setHasMore(false)
      }
    } catch (err) {
      console.error('Ошибка загрузки популярных аниме:', err)
      console.error('Тип ошибки:', err.isNetworkError ? 'Network Error' : 'API Error')
      console.error('Детали ошибки:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        url: err.config?.url
      })
      setHasError(true)
      setHasMore(false)
      // При ошибке показываем пустые карточки
      if (offset === 0) {
        setAnimeList(createEmptyCards(itemsPerPage))
      }
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    const nextPage = currentPage + 1
    const nextOffset = nextPage * itemsPerPage
    
    // Если у нас нет данных для следующей страницы, загружаем их
    if (nextOffset >= animeList.length && hasMore) {
      loadAnime(nextOffset)
    }
    
    setCurrentPage(nextPage)
    scrollToPage(nextPage)
  }

  const handlePrev = () => {
    if (currentPage > 0) {
      const prevPage = currentPage - 1
      setCurrentPage(prevPage)
      scrollToPage(prevPage)
    }
  }

  const scrollToPage = (page) => {
    if (carouselRef.current) {
      const scrollAmount = page * 100
      // Используем translate3d для GPU ускорения
      carouselRef.current.style.transform = `translate3d(-${scrollAmount}%, 0, 0)`
    }
  }

  // Всегда показываем секцию, даже если данных нет
  const displayList = animeList.length > 0 ? animeList : createEmptyCards(itemsPerPage)
  const totalPages = totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(displayList.length / itemsPerPage)

  return (
    <section className="popular-anime-section">
      <div className="container">
        <div className="section-header">
          <div className="section-title-wrapper">
            <h2 className="section-title">Популярное аниме</h2>
            {totalCount > 0 && Math.ceil(totalCount / itemsPerPage) > maxPagesToShow && !showAll && (
              <button 
                className="section-expand-btn"
                onClick={async () => {
                  setShowAll(true)
                  // Загружаем данные для всех страниц, если их еще нет
                  const totalPages = Math.ceil(totalCount / itemsPerPage)
                  const neededItems = totalPages * itemsPerPage
                  if (animeList.length < neededItems && hasMore) {
                    // Загружаем данные порциями
                    let currentOffset = animeList.length
                    while (currentOffset < neededItems && hasMore) {
                      await loadAnime(currentOffset)
                      currentOffset += itemsPerPage
                    }
                  }
                }}
                aria-label="Показать все аниме"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            )}
          </div>
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
                disabled={totalCount > 0 && currentPage >= (showAll ? Math.ceil(totalCount / itemsPerPage) : Math.min(maxPagesToShow, Math.ceil(totalCount / itemsPerPage))) - 1 && !hasMore}
                aria-label="Следующая страница"
              >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        </div>

        <div className="carousel-wrapper">
          <div className="carousel-container" ref={carouselRef}>
            {totalCount > 0 && Array.from({ length: showAll ? Math.ceil(totalCount / itemsPerPage) : Math.min(maxPagesToShow, Math.ceil(totalCount / itemsPerPage)) }, (_, pageIndex) => (
              <div key={pageIndex} className="carousel-page">
                {displayList.slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage).map((anime) => {
                  const isPlaceholder = anime.isPlaceholder || !anime.poster_url
                  
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
                  
                  const score = anime.score ? parseFloat(anime.score) : null
                  const scoreClass = getScoreClass(score)
                  const scoreDisplay = score ? score.toFixed(1) : null
                  
                  const posterContent = (
                    <div className="anime-card-poster">
                      {isPlaceholder ? (
                        <div className="placeholder-poster">
                          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                            <path d="M9 9h6v6H9z"/>
                          </svg>
                        </div>
                      ) : (
                        <>
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
                        </>
                      )}
                    </div>
                  )
                  
                  if (isPlaceholder) {
                    return (
                      <div
                        key={anime.id}
                        className="popular-anime-card-wrapper"
                      >
                        <div className="popular-anime-card placeholder-card">
                          {posterContent}
                        </div>
                        <div className="anime-card-title">{anime.title || 'Не определено'}</div>
                      </div>
                    )
                  }
                  
                  return (
                    <div key={anime.id} className="popular-anime-card-wrapper">
                      <Link
                        to={`/watch/${anime.id}`}
                        className="popular-anime-card"
                      >
                        {posterContent}
                      </Link>
                      <div className="anime-card-title">{anime.title || 'Не определено'}</div>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        {totalCount > 0 && (showAll ? Math.ceil(totalCount / itemsPerPage) : Math.min(maxPagesToShow, Math.ceil(totalCount / itemsPerPage))) > 1 && (
          <div className="carousel-indicators">
            {Array.from({ length: showAll ? Math.ceil(totalCount / itemsPerPage) : Math.min(maxPagesToShow, Math.ceil(totalCount / itemsPerPage)) }, (_, i) => (
              <button
                key={i}
                className={`indicator ${i === currentPage ? 'active' : ''}`}
                onClick={() => {
                  const targetOffset = i * itemsPerPage
                  // Если у нас нет данных для этой страницы, загружаем их
                  if (targetOffset >= animeList.length && hasMore) {
                    loadAnime(targetOffset)
                  }
                  setCurrentPage(i)
                  scrollToPage(i)
                }}
                aria-label={`Страница ${i + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

export default PopularAnimeCarousel


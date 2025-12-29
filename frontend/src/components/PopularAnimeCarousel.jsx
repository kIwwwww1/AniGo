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
  const carouselRef = useRef(null)
  const itemsPerPage = 6

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
    loadAnime(0)
  }, [])

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
      carouselRef.current.style.transform = `translateX(-${scrollAmount}%)`
    }
  }

  // Всегда показываем секцию, даже если данных нет
  const displayList = animeList.length > 0 ? animeList : createEmptyCards(itemsPerPage)
  const totalPages = Math.ceil(displayList.length / itemsPerPage)

  return (
    <section className="popular-anime-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Популярное аниме</h2>
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
              disabled={currentPage >= totalPages - 1 && !hasMore}
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
            {Array.from({ length: Math.ceil(displayList.length / itemsPerPage) }, (_, pageIndex) => (
              <div key={pageIndex} className="carousel-page">
                {displayList.slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage).map((anime) => {
                  const isPlaceholder = anime.isPlaceholder || !anime.poster_url
                  
                  const cardContent = (
                    <>
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
                            {anime.score && (
                              <div className="anime-card-score">
                                <span>★</span> {anime.score.toFixed(1)}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                      <div className="anime-card-title">{anime.title || 'Не определено'}</div>
                    </>
                  )
                  
                  if (isPlaceholder) {
                    return (
                      <div
                        key={anime.id}
                        className="popular-anime-card placeholder-card"
                      >
                        {cardContent}
                      </div>
                    )
                  }
                  
                  return (
                    <Link
                      key={anime.id}
                      to={`/watch/${anime.id}`}
                      className="popular-anime-card"
                    >
                      {cardContent}
                    </Link>
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        {Math.ceil(displayList.length / itemsPerPage) > 1 && (
          <div className="carousel-indicators">
            {Array.from({ length: Math.ceil(displayList.length / itemsPerPage) }, (_, i) => (
              <button
                key={i}
                className={`indicator ${i === currentPage ? 'active' : ''}`}
                onClick={() => {
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


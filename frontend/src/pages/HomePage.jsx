import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { animeAPI } from '../services/api'
import PopularAnimeCarousel from '../components/PopularAnimeCarousel'
import './HomePage.css'

function HomePage() {
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [offset, setOffset] = useState(0)
  const [currentPage, setCurrentPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const carouselRef = useRef(null)
  const limit = 12
  const itemsPerPage = 6
  const maxPagesToShow = 3

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
      console.error('Ошибка загрузки количества аниме:', err)
      setTotalCount(0)
    }
  }

  const loadAnime = async (loadOffset) => {
    try {
      setLoading(true)
      const response = await animeAPI.getAnimePaginated(limit, loadOffset)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (loadOffset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === limit)
      } else {
        setHasMore(false)
        if (loadOffset === 0) {
          setAnimeList([])
        }
      }
      setError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки аниме'
      setError(errorMessage)
      console.error('Ошибка загрузки аниме:', err)
      console.error('Детали ошибки:', err.response?.data)
      
      // При первой загрузке устанавливаем пустой список
      if (loadOffset === 0) {
        setAnimeList([])
      }
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    const nextPage = currentPage + 1
    const nextOffset = nextPage * itemsPerPage
    
    // Если у нас нет данных для следующей страницы, загружаем их
    if (nextOffset >= animeList.length && hasMore) {
      // Загружаем данные с нужного offset
      const loadOffset = Math.floor(animeList.length / limit) * limit
      loadAnime(loadOffset)
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

  return (
    <div className="home-page">
      <div className="container">
        <section className="hero">
          <h2 className="hero-title">Добро пожаловать в AniGo</h2>
          <p className="hero-subtitle">Смотрите лучшие аниме онлайн</p>
        </section>

        {/* Карусель популярных аниме */}
        <PopularAnimeCarousel />

        <section className="anime-section">
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">Каталог аниме</h2>
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
                        currentOffset += limit
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
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="carousel-wrapper">
            <div className="carousel-container" ref={carouselRef}>
              {totalCount > 0 && Array.from({ length: showAll ? Math.ceil(totalCount / itemsPerPage) : Math.min(maxPagesToShow, Math.ceil(totalCount / itemsPerPage)) }, (_, pageIndex) => (
                <div key={pageIndex} className="carousel-page">
                  {animeList.slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage).map((anime) => {
                    const score = anime.score ? parseFloat(anime.score) : null
                    const scoreClass = getScoreClass(score)
                    const scoreDisplay = score ? score.toFixed(1) : null

                    return (
                      <div key={anime.id} className="popular-anime-card-wrapper">
                        <Link
                          to={`/watch/${anime.id}`}
                          className="popular-anime-card"
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
                      // Загружаем данные порциями до нужной страницы
                      const loadOffset = Math.floor(animeList.length / limit) * limit
                      loadAnime(loadOffset)
                    }
                    setCurrentPage(i)
                    scrollToPage(i)
                  }}
                  aria-label={`Страница ${i + 1}`}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default HomePage


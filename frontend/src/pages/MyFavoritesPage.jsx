import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import './MyFavoritesPage.css'

function MyFavoritesPage() {
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(0)
  const navigate = useNavigate()
  const carouselRef = useRef(null)
  const itemsPerPage = 6

  useEffect(() => {
    loadFavorites()
  }, [])

  const loadFavorites = async () => {
    try {
      setLoading(true)
      const response = await userAPI.getFavorites()
      if (response.message) {
        setFavorites(Array.isArray(response.message) ? response.message : [])
      } else {
        setFavorites([])
      }
      setError(null)
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Необходимо войти в аккаунт для просмотра избранного')
        // Перенаправляем на главную через 2 секунды
        setTimeout(() => {
          navigate('/')
        }, 2000)
      } else {
        setError('Ошибка загрузки избранного')
        console.error('Ошибка загрузки избранного:', err)
      }
      setFavorites([])
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    const totalPages = Math.ceil(favorites.length / itemsPerPage)
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1)
      scrollToPage(currentPage + 1)
    }
  }

  const handlePrev = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
      scrollToPage(currentPage - 1)
    }
  }

  const scrollToPage = (page) => {
    if (carouselRef.current) {
      const scrollAmount = page * 100
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

  if (loading) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <div className="error-message">{error}</div>
        </div>
      </div>
    )
  }

  const totalPages = Math.ceil(favorites.length / itemsPerPage)

  return (
    <div className="my-favorites-page">
      <div className="container">
        <section className="popular-anime-section">
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">Мои избранные аниме</h2>
              {favorites.length > 0 && (
                <span className="favorites-count">Всего: {favorites.length}</span>
              )}
            </div>
            {favorites.length > itemsPerPage && (
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
                  disabled={currentPage >= totalPages - 1}
                  aria-label="Следующая страница"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 18l6-6-6-6"/>
                  </svg>
                </button>
              </div>
            )}
          </div>

          {favorites.length === 0 ? (
            <div className="empty-favorites">
              <div className="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </div>
              <h2 className="empty-title">У вас пока нет избранных аниме</h2>
              <p className="empty-description">
                Добавляйте аниме в избранное, нажимая на сердечко на странице просмотра
              </p>
            </div>
          ) : (
            <>
              <div className="carousel-wrapper">
                <div className="carousel-container" ref={carouselRef}>
                  {Array.from({ length: totalPages }, (_, pageIndex) => (
                    <div key={pageIndex} className="carousel-page">
                      {favorites.slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage).map((anime) => {
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

              {totalPages > 1 && (
                <div className="carousel-indicators">
                  {Array.from({ length: totalPages }, (_, i) => (
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
            </>
          )}
        </section>
      </div>
    </div>
  )
}

export default MyFavoritesPage


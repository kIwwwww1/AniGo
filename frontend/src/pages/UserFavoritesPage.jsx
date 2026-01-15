import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import '../components/AnimeCardGrid.css'
import './MyFavoritesPage.css'
import './AllAnimePage.css'

function UserFavoritesPage() {
  const { username } = useParams()
  const [allFavorites, setAllFavorites] = useState([])
  const [displayedFavorites, setDisplayedFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  const [user, setUser] = useState(null)
  const itemsPerRow = 6
  const limit = 12

  useEffect(() => {
    if (username) {
      loadFavorites()
    }
  }, [username])

  const loadFavorites = async () => {
    try {
      setLoading(true)
      const response = await userAPI.getUserProfile(username)
      if (response.message) {
        setUser(response.message)
        const favorites = response.message.favorites || []
        setAllFavorites(favorites)
        setDisplayedFavorites(favorites.slice(0, limit))
      } else {
        setAllFavorites([])
        setDisplayedFavorites([])
      }
      setError(null)
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Пользователь не найден')
      } else {
        setError('Ошибка загрузки избранного')
        console.error('Ошибка загрузки избранного:', err)
      }
      setAllFavorites([])
      setDisplayedFavorites([])
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = () => {
    if (!loadingMore && displayedFavorites.length < allFavorites.length) {
      setLoadingMore(true)
      setTimeout(() => {
        const nextBatch = allFavorites.slice(0, displayedFavorites.length + limit)
        setDisplayedFavorites(nextBatch)
        setLoadingMore(false)
      }, 300)
    }
  }

  const hasMore = displayedFavorites.length < allFavorites.length

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

  // Разбиваем список на строки по 6 элементов
  const rows = []
  for (let i = 0; i < displayedFavorites.length; i += itemsPerRow) {
    rows.push(displayedFavorites.slice(i, i + itemsPerRow))
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

  if (allFavorites.length === 0) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <section className="all-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Избранные аниме пользователя {user?.username || username}</h2>
                <p className="favorites-count">Всего: 0</p>
              </div>
            </div>
            <div className="empty-favorites">
              <div className="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </div>
              <h3 className="empty-title">У пользователя нет избранных аниме</h3>
              <p className="empty-description">
                Пользователь еще не добавил аниме в избранное
              </p>
            </div>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="my-favorites-page">
      <div className="container">
        <section className="all-anime-section">
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">Избранные аниме пользователя {user?.username || username}</h2>
              <p className="favorites-count">Всего: {allFavorites.length}</p>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {displayedFavorites.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              Нет избранных аниме
            </div>
          ) : (
            <>
              <div className="all-anime-grid">
                {rows.map((row, rowIndex) => (
                  <div key={rowIndex} className="all-anime-row">
                    {row.map((anime) => {
                      const score = anime.score ? parseFloat(anime.score) : null
                      const scoreClass = getScoreClass(score)
                      const scoreDisplay = score ? score.toFixed(1) : null

                      return (
                        <div key={anime.id} className="all-anime-item">
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

              {hasMore && (
                <div className="load-more-container">
                  <button 
                    className="load-more-btn"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Загрузка...' : 'Показать больше'}
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  )
}

export default UserFavoritesPage

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { animeAPI } from '../services/api'
import '../components/AnimeCardGrid.css'
import './AllAnimePage.css'

function AllAnimePage() {
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const limit = 12
  const itemsPerRow = 6

  useEffect(() => {
    loadAnime(0)
  }, [])

  const loadAnime = async (offset) => {
    try {
      setLoading(true)
      const response = await animeAPI.getAllAnime(limit, offset)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (offset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === limit)
      } else {
        setHasMore(false)
        if (offset === 0) {
          setAnimeList([])
        }
      }
      setError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки аниме'
      setError(errorMessage)
      console.error('Ошибка загрузки аниме:', err)
      setHasMore(false)
      if (offset === 0) {
        setAnimeList([])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      loadAnime(animeList.length)
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

  // Разбиваем список на строки по 6 элементов
  const rows = []
  for (let i = 0; i < animeList.length; i += itemsPerRow) {
    rows.push(animeList.slice(i, i + itemsPerRow))
  }

  if (loading && animeList.length === 0) {
    return (
      <div className="all-anime-page">
        <div className="container">
          <section className="all-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Каталог аниме</h2>
              </div>
            </div>
            <div className="loading">Загрузка...</div>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="all-anime-page">
      <div className="container">
        <section className="all-anime-section">
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">Каталог аниме</h2>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {animeList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              Нет аниме в каталоге
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
                    disabled={loading}
                  >
                    {loading ? 'Загрузка...' : 'Показать больше'}
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

export default AllAnimePage


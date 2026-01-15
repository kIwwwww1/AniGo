import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { animeAPI, userAPI } from '../services/api'
import '../components/AnimeCardGrid.css'
import './PopularAnimePage.css'

function PopularAnimePage() {
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const limit = 12
  const itemsPerRow = 6

  useEffect(() => {
    loadAnime(0)
    loadAvatarBorderColor()
  }, [])

  // Загружаем цвет обводки аватарки и устанавливаем в CSS переменную
  const loadAvatarBorderColor = async () => {
    try {
      const response = await userAPI.getCurrentUser()
      if (response && response.message && response.message.username) {
        // Загружаем настройки профиля из API
        const settingsResponse = await userAPI.getProfileSettings()
        if (settingsResponse.message && settingsResponse.message.avatar_border_color) {
          const savedColor = settingsResponse.message.avatar_border_color
          const availableColors = ['#ffffff', '#000000', '#808080', '#c4c4af', '#0066ff', '#00cc00', '#ff0000', '#ff69b4', '#ffd700', '#9932cc']
          
          if (availableColors.includes(savedColor)) {
            // Сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
            localStorage.setItem('user-avatar-border-color', savedColor)
            // Устанавливаем CSS переменную
            document.documentElement.style.setProperty('--user-accent-color', savedColor)
            
            // Создаем rgba версию для hover эффектов
            const hex = savedColor.replace('#', '')
            const r = parseInt(hex.slice(0, 2), 16)
            const g = parseInt(hex.slice(2, 4), 16)
            const b = parseInt(hex.slice(4, 6), 16)
            const rgba = `rgba(${r}, ${g}, ${b}, 0.1)`
            document.documentElement.style.setProperty('--user-accent-color-rgba', rgba)
            
            // Создаем тень для box-shadow
            const shadowRgba = `rgba(${r}, ${g}, ${b}, 0.4)`
            document.documentElement.style.setProperty('--user-accent-color-shadow', shadowRgba)
          }
        }
      }
    } catch (err) {
      // Пользователь не авторизован, игнорируем
    }
  }

  // Слушаем изменения цвета обводки
  useEffect(() => {
    const handleAvatarBorderColorUpdate = () => {
      loadAvatarBorderColor()
    }
    window.addEventListener('avatarBorderColorUpdated', handleAvatarBorderColorUpdate)
    return () => {
      window.removeEventListener('avatarBorderColorUpdated', handleAvatarBorderColorUpdate)
    }
  }, [])

  const loadAnime = async (offset) => {
    try {
      setLoading(true)
      const response = await animeAPI.getAllPopularAnime(limit, offset)
      
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
      console.error('Ошибка загрузки популярных аниме:', err)
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
      <div className="popular-anime-page">
        <div className="container">
          <section className="popular-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Популярное аниме</h2>
              </div>
            </div>
            <div className="loading">Загрузка...</div>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="popular-anime-page">
      <div className="container">
        <section className="popular-anime-section">
          <div className="section-header">
            <div className="section-title-wrapper">
              <h2 className="section-title">Популярное аниме</h2>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {animeList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              Нет популярных аниме
            </div>
          ) : (
            <>
              <div className="popular-anime-grid">
                {rows.map((row, rowIndex) => (
                  <div key={rowIndex} className="popular-anime-row">
                    {row.map((anime) => {
                      const score = anime.score ? parseFloat(anime.score) : null
                      const scoreClass = getScoreClass(score)
                      const scoreDisplay = score ? score.toFixed(1) : null

                      return (
                        <div key={anime.id} className="popular-anime-item">
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

export default PopularAnimePage


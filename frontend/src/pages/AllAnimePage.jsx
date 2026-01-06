import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { animeAPI, userAPI } from '../services/api'
import '../components/AnimeCardGrid.css'
import './AllAnimePage.css'

function AllAnimePage() {
  const [searchParams] = useSearchParams()
  const studioName = searchParams.get('studio')
  const genreName = searchParams.get('genre')
  
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [sortBy, setSortBy] = useState('none') // 'none', 'score_asc', 'score_desc'
  const limit = 12
  const itemsPerRow = 6

  const loadAnime = useCallback(async (offset) => {
    try {
      setLoading(true)
      let response
      
      // Если есть фильтр по студии, используем его
      if (studioName) {
        response = await animeAPI.getAnimeByStudio(studioName, limit, offset)
      }
      // Если есть фильтр по жанру, используем его
      else if (genreName) {
        response = await animeAPI.getAnimeByGenre(genreName, limit, offset)
      }
      // Выбираем API в зависимости от сортировки
      else if (sortBy === 'score_asc') {
        // Сортировка по оценке по возрастанию (низкая → высокая)
        response = await animeAPI.getAnimeByScore('asc', limit, offset)
      } else if (sortBy === 'score_desc') {
        // Сортировка по оценке по убыванию (высокая → низкая)
        response = await animeAPI.getAnimeByScore('desc', limit, offset)
      } else {
        // Без сортировки
        response = await animeAPI.getAllAnime(limit, offset)
      }
      
      // Обрабатываем ответ - может быть массив или объект с message
      let animeData = Array.isArray(response.message) 
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
  }, [sortBy, limit, studioName, genreName])

  useEffect(() => {
    loadAnime(0)
    loadAvatarBorderColor()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Загружаем только при монтировании компонента

  useEffect(() => {
    // Перезагружаем данные при изменении сортировки или студии
    loadAnime(0)
  }, [loadAnime]) // loadAnime зависит от sortBy и studioName, поэтому это сработает при изменении

  // Загружаем цвет обводки аватарки и устанавливаем в CSS переменную
  const loadAvatarBorderColor = async () => {
    try {
      const response = await userAPI.getCurrentUser()
      if (response && response.message && response.message.username) {
        const username = response.message.username
        const savedColor = localStorage.getItem(`user_${username}_avatar_border_color`)
        const availableColors = ['#ffffff', '#000000', '#808080', '#c4c4af', '#0066ff', '#00cc00', '#ff0000', '#ff69b4', '#ffd700', '#9932cc']
        
        if (savedColor && availableColors.includes(savedColor)) {
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
              <h2 className="section-title">
                {studioName 
                  ? `Аниме студии: ${studioName}` 
                  : genreName 
                    ? `Аниме жанра: ${genreName}`
                    : 'Каталог аниме'}
              </h2>
            </div>
            <div className="sort-controls">
              <label htmlFor="sort-select" className="sort-label">Сортировка:</label>
              <select 
                id="sort-select"
                className="sort-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                disabled={loading}
              >
                <option value="none">Без сортировки</option>
                <option value="score_desc">По оценке (высокая → низкая)</option>
                <option value="score_asc">По оценке (низкая → высокая)</option>
              </select>
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


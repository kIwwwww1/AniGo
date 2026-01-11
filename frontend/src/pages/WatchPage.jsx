import { useState, useEffect, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { animeAPI, userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import VideoPlayer from '../components/VideoPlayer'
import AnimeCard from '../components/AnimeCard'
import CrownIcon from '../components/CrownIcon'
import './WatchPage.css'

function WatchPage() {
  const { animeId } = useParams()
  const navigate = useNavigate()
  const [anime, setAnime] = useState(null)
  const [randomAnime, setRandomAnime] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [authError, setAuthError] = useState(false)
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [commentText, setCommentText] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false)
  const [userRating, setUserRating] = useState(null)
  const [tempRating, setTempRating] = useState(5) // Временное значение для слайдера
  const [submittingRating, setSubmittingRating] = useState(false)
  const [isRatingMenuOpen, setIsRatingMenuOpen] = useState(false)
  const [isFavorite, setIsFavorite] = useState(false)
  const [openReportMenu, setOpenReportMenu] = useState(null) // ID комментария, для которого открыто меню
  const [comments, setComments] = useState([]) // Комментарии с пагинацией
  const [commentsPage, setCommentsPage] = useState(0) // Текущая страница комментариев
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsHasMore, setCommentsHasMore] = useState(true)
  const [hasAnyComments, setHasAnyComments] = useState(false) // Есть ли комментарии вообще
  const [avatarErrors, setAvatarErrors] = useState({}) // Ошибки загрузки аватарок комментариев
  const [mousePosition, setMousePosition] = useState({ x: 0.5, y: 0.5 }) // Позиция мыши для голографического эффекта
  const [isHoveringPoster, setIsHoveringPoster] = useState(false) // Наведена ли мышь на постер
  const commentsLimit = 4 // Количество комментариев на странице
  
  // useRef для debounce автоматического подтверждения рейтинга
  const ratingTimeoutRef = useRef(null)

  useEffect(() => {
    // Прокручиваем страницу вверх при переходе на страницу аниме
    window.scrollTo(0, 0)
    
    // Сбрасываем все состояния при смене аниме
    setUserRating(null)
    setTempRating(5)
    setIsRatingMenuOpen(false)
    setIsFavorite(false)
    setComments([])
    setCommentsPage(0)
    setCommentsHasMore(true)
    setHasAnyComments(false)
    
    loadAnime()
    loadRandomAnime()
    checkFavoriteStatus()
    checkUserRating()
    loadComments(0) // Загружаем первую страницу комментариев
    loadAvatarBorderColor() // Загружаем цвет обводки аватарки
  }, [animeId])

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

  // Автоматическое подтверждение рейтинга после остановки движения слайдера
  useEffect(() => {
    if (isRatingMenuOpen && tempRating !== userRating) {
      // Очищаем предыдущий таймер
      if (ratingTimeoutRef.current) {
        clearTimeout(ratingTimeoutRef.current)
      }
      
      // Устанавливаем новый таймер на 1 секунду
      ratingTimeoutRef.current = setTimeout(() => {
        handleSubmitRating(tempRating)
      }, 1000)
    }
    
    // Cleanup при размонтировании
    return () => {
      if (ratingTimeoutRef.current) {
        clearTimeout(ratingTimeoutRef.current)
      }
    }
  }, [tempRating, isRatingMenuOpen])

  useEffect(() => {
    if (anime && anime.players && anime.players.length > 0) {
      // Используем первый доступный плеер
      const player = anime.players[0]
      if (player) {
        setSelectedPlayer({
          ...player,
          embed_url: player.embed_url
        })
      }
    }
  }, [anime])

  useEffect(() => {
    // Закрываем меню рейтинга при клике вне его
    const handleClickOutside = (event) => {
      if (isRatingMenuOpen && !event.target.closest('.rating-button-wrapper')) {
        setIsRatingMenuOpen(false)
      }
      if (openReportMenu !== null && !event.target.closest('.comment-menu-wrapper')) {
        setOpenReportMenu(null)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isRatingMenuOpen, openReportMenu])

  const loadAnime = async () => {
    try {
      setLoading(true)
      setAuthError(false)
      const response = await animeAPI.getAnimeById(animeId)
      if (response.message) {
        setAnime(response.message)
      }
      setError(null)
    } catch (err) {
      if (err.response?.status === 401) {
        // Пользователь не авторизован
        setAuthError(true)
        setError('Для просмотра аниме необходимо войти в аккаунт')
      } else if (err.response?.status === 403) {
        // Пользователь заблокирован
        setAuthError(true)
        setError('Ваш аккаунт заблокирован. Доступ к просмотру аниме ограничен.')
      } else {
        setError('Ошибка загрузки аниме')
        console.error(err)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadComments = async (page = 0) => {
    if (!animeId) return
    
    try {
      setCommentsLoading(true)
      const offset = page * commentsLimit
      const response = await animeAPI.getCommentsPaginated(parseInt(animeId), commentsLimit, offset)
      
      if (response.message) {
        const newComments = Array.isArray(response.message) ? response.message : []
        
        // Если мы перешли на пустую страницу (не первую), возвращаемся на предыдущую
        if (page > 0 && newComments.length === 0) {
          // Возвращаемся на предыдущую страницу
          await loadComments(page - 1)
          return
        }
        
        setComments(newComments) // Всегда заменяем комментарии, а не добавляем
        // Следующая страница есть только если мы получили ровно commentsLimit комментариев
        // Это означает, что может быть еще комментарии на следующей странице
        setCommentsHasMore(newComments.length === commentsLimit)
        setCommentsPage(page)
        
        // Если на первой странице есть комментарии, значит комментарии есть вообще
        if (page === 0) {
          setHasAnyComments(newComments.length > 0)
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки комментариев:', err)
    } finally {
      setCommentsLoading(false)
    }
  }

  const updateComments = async () => {
    // Перезагружаем текущую страницу комментариев после добавления нового
    await loadComments(0) // Всегда возвращаемся на первую страницу после добавления комментария
  }

  const handleNextCommentsPage = async () => {
    if (!commentsLoading && commentsHasMore) {
      // Проверяем следующую страницу перед переходом
      const nextPage = commentsPage + 1
      const offset = nextPage * commentsLimit
      try {
        const response = await animeAPI.getCommentsPaginated(parseInt(animeId), commentsLimit, offset)
        const nextComments = Array.isArray(response.message) ? response.message : []
        
        // Если следующая страница пустая, не переходим
        if (nextComments.length === 0) {
          setCommentsHasMore(false)
          return
        }
        
        // Если следующая страница не пустая, переходим
        await loadComments(nextPage)
      } catch (err) {
        console.error('Ошибка проверки следующей страницы:', err)
      }
    }
  }

  const handlePrevCommentsPage = () => {
    if (!commentsLoading && commentsPage > 0) {
      loadComments(commentsPage - 1)
    }
  }

  const updateRating = async () => {
    // Обновляем только рейтинг без перезагрузки всей страницы
    try {
      const response = await animeAPI.getAnimeById(animeId)
      if (response.message && anime) {
        // Обновляем только рейтинг, сохраняя остальные данные
        setAnime({
          ...anime,
          score: response.message.score || anime.score
        })
      }
    } catch (err) {
      console.error('Ошибка обновления рейтинга:', err)
    }
  }

  const loadRandomAnime = async () => {
    try {
      const response = await animeAPI.getRandomAnime(3)
      if (response.message) {
        setRandomAnime(response.message)
      }
    } catch (err) {
      console.error('Ошибка загрузки случайных аниме:', err)
    }
  }

  const checkFavoriteStatus = async () => {
    try {
      const response = await userAPI.checkFavorite(parseInt(animeId))
      if (response.message && response.message.is_favorite !== undefined) {
        setIsFavorite(response.message.is_favorite)
      }
    } catch (err) {
      // Если пользователь не авторизован, просто игнорируем ошибку
      if (err.response?.status !== 401) {
        console.error('Ошибка проверки избранного:', err)
      }
    }
  }

  const checkUserRating = async () => {
    try {
      const response = await userAPI.checkRating(parseInt(animeId))
      if (response.message && response.message.rating !== null && response.message.rating !== undefined) {
        setUserRating(response.message.rating)
      }
    } catch (err) {
      // Если пользователь не авторизован, просто игнорируем ошибку
      if (err.response?.status !== 401) {
        console.error('Ошибка проверки оценки:', err)
      }
    }
  }

  const handleSubmitComment = async (e) => {
    e.preventDefault()
    if (!commentText.trim()) return

    try {
      setSubmittingComment(true)
      await userAPI.createComment(parseInt(animeId), commentText)
      setCommentText('')
      // Обновляем только комментарии без перезагрузки всей страницы
      await updateComments()
    } catch (err) {
      console.error('Ошибка при отправке комментария:', err)
      alert('Ошибка при отправке комментария')
    } finally {
      setSubmittingComment(false)
    }
  }

  const handleSubmitRating = async (rating) => {
    if (rating < 1 || rating > 10) return

    try {
      setSubmittingRating(true)
      await userAPI.createRating(parseInt(animeId), rating)
      setUserRating(rating)
      setIsRatingMenuOpen(false)
      // Обновляем только рейтинг без перезагрузки всей страницы
      await updateRating()
    } catch (err) {
      console.error('Ошибка при отправке рейтинга:', err)
      alert(err.response?.data?.detail || 'Ошибка при отправке рейтинга')
    } finally {
      setSubmittingRating(false)
    }
  }

  const handleToggleFavorite = async () => {
    try {
      const response = await userAPI.toggleFavorite(parseInt(animeId))
      console.log('Toggle favorite response:', response)
      
      // Обновляем состояние на основе ответа
      if (response && 'is_favorite' in response) {
        setIsFavorite(response.is_favorite)
      } else if (response.message && typeof response.message === 'object' && 'is_favorite' in response.message) {
        setIsFavorite(response.message.is_favorite)
      } else {
        // Если структура неожиданная, перепроверяем статус
        await checkFavoriteStatus()
      }
    } catch (err) {
      if (err.response?.status === 401) {
        alert('Необходимо войти в аккаунт для добавления в избранное')
      } else {
        console.error('Ошибка при работе с избранным:', err)
        alert('Ошибка при работе с избранным')
      }
      // В случае ошибки перепроверяем статус
      await checkFavoriteStatus()
    }
  }

  const handleReportComment = async (commentId) => {
    try {
      // TODO: Реализовать API для жалобы на комментарий
      alert('Жалоба отправлена. Спасибо за обратную связь!')
      setOpenReportMenu(null)
    } catch (err) {
      console.error('Ошибка при отправке жалобы:', err)
      alert('Ошибка при отправке жалобы')
    }
  }

  const toggleReportMenu = (commentId) => {
    setOpenReportMenu(openReportMenu === commentId ? null : commentId)
  }

  const handlePosterMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    setMousePosition({ x, y })
    setIsHoveringPoster(true)
  }

  const handlePosterMouseLeave = () => {
    setIsHoveringPoster(false)
    setMousePosition({ x: 0.5, y: 0.5 })
  }

  if (loading) {
    return (
      <div className="watch-page">
        <div className="container">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    )
  }

  if (error || !anime) {
    return (
      <div className="watch-page">
        <div className="container">
          <div className="error-message">
            {error || 'Аниме не найдено'}
            {authError && (
              <div style={{ marginTop: '20px' }}>
                <button
                  onClick={() => navigate('/')}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#e50914',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  Вернуться на главную
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="watch-page">
      <div className="container">
        {/* Верхняя часть: постер слева, данные справа */}
        <div className="watch-header-section">
          <div 
            className="anime-poster-container"
            onMouseMove={handlePosterMouseMove}
            onMouseLeave={handlePosterMouseLeave}
          >
            <div 
              className={`holographic-poster-wrapper ${isHoveringPoster ? 'hover' : ''}`}
              style={{
                '--mouse-x': mousePosition.x,
                '--mouse-y': mousePosition.y,
              }}
            >
              <img
                src={anime.poster_url || '/placeholder.jpg'}
                alt={anime.title}
                className="anime-poster-main"
              />
              {anime.score && (
                <div className="anime-score-badge">
                  <span>★</span> {anime.score.toFixed(1)}
                </div>
              )}
            </div>
          </div>
          
          <div className="anime-info-section">
            <div className="anime-title-wrapper">
              <h1 className="anime-title-main">{anime.title}</h1>
              {anime.title_original && (
                <p className="anime-original-title">{anime.title_original}</p>
              )}
            </div>
            
            <div className="anime-details-grid">
              {(anime.studio || (anime.genres && anime.genres.length > 0)) && (
                <div className="sort-info-tooltip details-grid-tooltip">
                  <span className="tooltip-icon">?</span>
                  <div className="tooltip-content">
                    {anime.studio && (
                      <div>Нажмите на название студии, чтобы увидеть все аниме от этой студии</div>
                    )}
                    {anime.studio && anime.genres && anime.genres.length > 0 && (
                      <div className="tooltip-divider"></div>
                    )}
                    {anime.genres && anime.genres.length > 0 && (
                      <div>Нажмите на название жанра, чтобы увидеть все аниме с этим жанром</div>
                    )}
                  </div>
                </div>
              )}
              
              {anime.score && (
                <div className="detail-row">
                  <span className="detail-label">Оценка</span>
                  <span className="detail-value">★ {anime.score.toFixed(1)}</span>
                </div>
              )}
              
              {anime.status && (
                <div className="detail-row">
                  <span className="detail-label">Статус</span>
                  <span className="detail-value">{anime.status}</span>
                </div>
              )}
              
              {anime.type && (
                <div className="detail-row">
                  <span className="detail-label">Тип</span>
                  <span className="detail-value">{anime.type}</span>
                </div>
              )}
              
              {anime.year && (
                <div className="detail-row">
                  <span className="detail-label">Год</span>
                  <span className="detail-value">{anime.year}</span>
                </div>
              )}
              
              {anime.episodes_count && (
                <div className="detail-row">
                  <span className="detail-label">Эпизодов</span>
                  <span className="detail-value">{anime.episodes_count}</span>
                </div>
              )}
              
              {anime.studio && (
                <div className="detail-row">
                  <span className="detail-label">Студия</span>
                  <Link 
                    to={`/anime/all/anime?studio=${encodeURIComponent(anime.studio)}`}
                    className="detail-value studio-link"
                  >
                    {anime.studio}
                  </Link>
                </div>
              )}
              
              {anime.rating && (
                <div className="detail-row">
                  <span className="detail-label">Рейтинг</span>
                  <span className="detail-value">{anime.rating}</span>
                </div>
              )}
              
              {anime.genres && anime.genres.length > 0 && (
                <div className="detail-row detail-row-genres">
                  <span className="detail-label">Жанры</span>
                  <div className="genres-tags">
                    {anime.genres.map((genre) => (
                      <Link
                        key={genre.id}
                        to={`/anime/all/anime?genre=${encodeURIComponent(genre.name)}`}
                        className="genre-tag genre-link"
                      >
                        {genre.name}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {anime.description && anime.description !== 'Нет описания' && (
              <div className="anime-description-section">
                <h3 className="section-title">Обзор</h3>
                <div className={`description-wrapper ${isDescriptionExpanded ? 'expanded' : ''}`}>
                  <p className="anime-description-text">
                    {isDescriptionExpanded || anime.description.length <= 250
                      ? anime.description
                      : `${anime.description.substring(0, 250)}...`}
                  </p>
                  {anime.description.length > 250 && (
                    <button
                      onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                      className={`description-toggle-btn ${isDescriptionExpanded ? 'expanded' : ''}`}
                      aria-label={isDescriptionExpanded ? 'Свернуть' : 'Развернуть'}
                    >
                      <svg 
                        width="20" 
                        height="20" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2"
                      >
                        <path d="M9 18l6-6-6-6"/>
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Основной контент: плеер слева, случайные аниме справа */}
        <div className="watch-content-section">
          <div className="watch-main-content">
            {/* Видеоплеер */}
            <div className="video-player-container">
              {selectedPlayer ? (
                <VideoPlayer player={selectedPlayer} />
              ) : (
                <div className="no-player">Плеер не доступен</div>
              )}
            </div>

            {/* Рекомендация по uBlock Origin */}
            <div className="player-recommendation">
              <p className="player-recommendation-text">
                Чтобы избежать показа рекламы во время просмотра, мы рекомендуем установить расширение{" "}
                <a
                  href="https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh?hl=ru"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="player-recommendation-link"
                >
                  uBlock Origin Lite
                </a>{" "}
                из официального магазина расширений Google Chrome
              </p>
              <p className="player-disclaimer">это не является рекламой, и мы никого не обязываем его устанавливать</p>
            </div>

            {/* Кнопки действий: Оценить и Избранное */}
            <div className="player-actions">
              <div className="rating-button-wrapper">
                {!isRatingMenuOpen ? (
                  <button
                    type="button"
                    onClick={() => {
                      // Инициализируем временное значение при открытии меню
                      setTempRating(userRating || 5)
                      setIsRatingMenuOpen(true)
                    }}
                    className="rate-button"
                    disabled={submittingRating}
                  >
                    {userRating ? `Оценка: ${userRating}` : 'Оценить'}
                  </button>
                ) : (
                  <div className="rating-menu">
                    <div className="rating-slider-container">
                      <span className="rating-slider-value">
                        <span className="rating-star">★</span>
                        {tempRating}
                      </span>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        step="1"
                        value={tempRating}
                        onChange={(e) => setTempRating(parseInt(e.target.value))}
                        className="rating-slider"
                        disabled={submittingRating}
                        style={{
                          background: `linear-gradient(to right, var(--user-accent-color, var(--accent)) 0%, var(--user-accent-color, var(--accent)) ${(tempRating - 1) * 11.11}%, var(--bg-secondary) ${(tempRating - 1) * 11.11}%, var(--bg-secondary) 100%)`
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={handleToggleFavorite}
                className={`favorite-button ${isFavorite ? 'active' : ''}`}
                aria-label={isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'}
              >
                <svg 
                  width="24" 
                  height="24" 
                  viewBox="0 0 24 24" 
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="favorite-heart-icon"
                >
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </button>
            </div>

            {/* Комментарии */}
            <div className="comments-section">
              <h3 className="section-title">Комментарии</h3>
              
              {/* Форма для нового комментария */}
              <form onSubmit={handleSubmitComment} className="comment-form">
                <div className="comment-input-wrapper">
                  <textarea
                    value={commentText}
                    onChange={(e) => {
                      if (e.target.value.length <= 100) {
                        setCommentText(e.target.value)
                      }
                    }}
                    onKeyDown={(e) => {
                      // Отправка при нажатии Enter/Return без Shift
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        if (commentText.trim() && !submittingComment) {
                          handleSubmitComment(e)
                        }
                      }
                    }}
                    placeholder="Оставьте пару слов..."
                    className="comment-input"
                    rows="3"
                    maxLength={100}
                  />
                  <div className="comment-char-count">
                    {commentText.length}/100
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={submittingComment || !commentText.trim()}
                  className="comment-submit-btn"
                >
                  {submittingComment ? 'Отправка...' : 'Отправить'}
                </button>
              </form>

              {/* Список комментариев */}
              <div className="comments-list">
                {commentsLoading && comments.length === 0 ? (
                  <p className="no-comments">Загрузка комментариев...</p>
                ) : comments.length > 0 ? (
                  comments.map((comment) => (
                    <div key={comment.id} className="comment-item">
                      <div className="comment-header">
                        <div className="comment-user">
                          {(() => {
                            const avatarUrl = normalizeAvatarUrl(comment.user?.avatar_url)
                            const hasError = avatarErrors[comment.id]
                            if (avatarUrl && !hasError) {
                              return (
                                <img
                                  src={avatarUrl}
                                  alt={comment.user?.username || 'User'}
                                  className="comment-avatar"
                                  onError={() => setAvatarErrors(prev => ({ ...prev, [comment.id]: true }))}
                                  onLoad={() => setAvatarErrors(prev => {
                                    const newErrors = { ...prev }
                                    delete newErrors[comment.id]
                                    return newErrors
                                  })}
                                />
                              )
                            }
                            return (
                              <div className="comment-avatar avatar-fallback" style={{ backgroundColor: '#000000' }}>
                                <span>🐱</span>
                              </div>
                            )
                          })()}
                          <div className="comment-user-info">
                            {comment.user?.username ? (
                              <Link 
                                to={`/profile/${comment.user.username}`} 
                                className={`comment-username ${comment.user?.id < 100 ? 'premium-user' : ''}`}
                              >
                                {comment.user.username}
                                {comment.user?.id < 100 && (
                                  <span className="crown-icon-small">
                                    <CrownIcon size={14} />
                                  </span>
                                )}
                              </Link>
                            ) : (
                              <span className="comment-username">Неизвестный</span>
                            )}
                            <p className="comment-text">{comment.text}</p>
                          </div>
                        </div>
                        <div className="comment-header-right">
                          <span className="comment-date">{formatDate(comment.created_at)}</span>
                          <div className="comment-menu-wrapper">
                            <button
                              type="button"
                              className="comment-menu-btn"
                              onClick={() => toggleReportMenu(comment.id)}
                              aria-label="Меню комментария"
                            >
                              <svg
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <circle cx="12" cy="5" r="1" />
                                <circle cx="12" cy="12" r="1" />
                                <circle cx="12" cy="19" r="1" />
                              </svg>
                            </button>
                            {openReportMenu === comment.id && (
                              <div className="comment-report-menu">
                                <button
                                  type="button"
                                  className="comment-report-btn"
                                  onClick={() => handleReportComment(comment.id)}
                                >
                                  Пожаловаться
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="no-comments">
                    {hasAnyComments 
                      ? 'На этой странице нет комментариев' 
                      : 'Пока нет комментариев. Будьте первым!'}
                  </p>
                )}
              </div>

              {/* Пагинация комментариев */}
              {(hasAnyComments || commentsPage > 0 || commentsHasMore) && (
                <div className="comments-pagination">
                  <button
                    type="button"
                    className="comments-pagination-btn"
                    onClick={handlePrevCommentsPage}
                    disabled={commentsLoading || commentsPage === 0}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M15 18l-6-6 6-6"/>
                    </svg>
                    Назад
                  </button>
                  
                  <span className="comments-page-info">
                    Страница {commentsPage + 1}
                  </span>
                  
                  <button
                    type="button"
                    className="comments-pagination-btn"
                    onClick={handleNextCommentsPage}
                    disabled={commentsLoading || !commentsHasMore}
                  >
                    Вперед
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 18l6-6-6-6"/>
                    </svg>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Боковая панель со случайными аниме */}
          <div className="watch-sidebar-content">
            <h3 className="sidebar-title">Похожее</h3>
            <div className="random-anime-list">
              {randomAnime.map((randomAnimeItem) => (
                <AnimeCard key={randomAnimeItem.id} anime={randomAnimeItem} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WatchPage

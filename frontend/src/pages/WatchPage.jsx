import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { animeAPI, userAPI } from '../services/api'
import VideoPlayer from '../components/VideoPlayer'
import AnimeCard from '../components/AnimeCard'
import './WatchPage.css'

function WatchPage() {
  const { animeId } = useParams()
  const [anime, setAnime] = useState(null)
  const [randomAnime, setRandomAnime] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [commentText, setCommentText] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false)
  const [userRating, setUserRating] = useState(null)
  const [submittingRating, setSubmittingRating] = useState(false)
  const [isRatingMenuOpen, setIsRatingMenuOpen] = useState(false)
  const [isFavorite, setIsFavorite] = useState(false)
  const [openReportMenu, setOpenReportMenu] = useState(null) // ID комментария, для которого открыто меню

  useEffect(() => {
    // Прокручиваем страницу вверх при переходе на страницу аниме
    window.scrollTo(0, 0)
    loadAnime()
    loadRandomAnime()
    checkFavoriteStatus()
  }, [animeId])

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
      const response = await animeAPI.getAnimeById(animeId)
      if (response.message) {
        setAnime(response.message)
      }
      setError(null)
    } catch (err) {
      setError('Ошибка загрузки аниме')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const updateComments = async () => {
    // Обновляем только комментарии без перезагрузки всей страницы
    try {
      const response = await animeAPI.getAnimeById(animeId)
      if (response.message && anime) {
        // Обновляем только комментарии, сохраняя остальные данные
        setAnime({
          ...anime,
          comments: response.message.comments || []
        })
      }
    } catch (err) {
      console.error('Ошибка обновления комментариев:', err)
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
      if (response.message && response.message.is_favorite !== undefined) {
        setIsFavorite(response.message.is_favorite)
      }
    } catch (err) {
      if (err.response?.status === 401) {
        alert('Необходимо войти в аккаунт для добавления в избранное')
      } else {
        console.error('Ошибка при работе с избранным:', err)
        alert('Ошибка при работе с избранным')
      }
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
          <div className="error-message">{error || 'Аниме не найдено'}</div>
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
          <div className="anime-poster-container">
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
          
          <div className="anime-info-section">
            <div className="anime-title-wrapper">
              <h1 className="anime-title-main">{anime.title}</h1>
              {anime.title_original && (
                <p className="anime-original-title">{anime.title_original}</p>
              )}
            </div>
            
            <div className="anime-details-grid">
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
                  <span className="detail-value">{anime.studio}</span>
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
                      <span key={genre.id} className="genre-tag">
                        {genre.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {anime.description && (
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

            {/* Кнопки действий: Оценить и Избранное */}
            <div className="player-actions">
              <div className="rating-button-wrapper">
                <button
                  type="button"
                  onClick={() => setIsRatingMenuOpen(!isRatingMenuOpen)}
                  className="rate-button"
                  disabled={submittingRating}
                >
                  {userRating ? `Оценка: ${userRating}` : 'Оценить'}
                </button>
                {isRatingMenuOpen && (
                  <div className="rating-menu">
                    <div className="rating-stars-menu">
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          onClick={() => handleSubmitRating(rating)}
                          disabled={submittingRating}
                          className={`rating-star-btn-menu ${userRating === rating ? 'selected' : ''}`}
                          title={`Оценить на ${rating}`}
                        >
                          <span className="rating-star">★</span>
                          <span className="rating-number">{rating}</span>
                        </button>
                      ))}
                    </div>
                    {submittingRating && (
                      <p className="rating-submitting">Отправка...</p>
                    )}
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
                  fill={isFavorite ? "#e50914" : "none"}
                  stroke={isFavorite ? "#e50914" : "currentColor"}
                  strokeWidth="2"
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
                {anime.comments && anime.comments.length > 0 ? (
                  [...anime.comments]
                    .sort((a, b) => {
                      // Сортируем от нового к старому
                      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
                      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
                      return dateB - dateA // Обратный порядок (новые первыми)
                    })
                    .map((comment) => (
                      <div key={comment.id} className="comment-item">
                        <div className="comment-header">
                          <div className="comment-user">
                            {comment.user.avatar_url && (
                              <img
                                src={comment.user.avatar_url}
                                alt={comment.user.username}
                                className="comment-avatar"
                              />
                            )}
                            <span className="comment-username">{comment.user.username}</span>
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
                        <p className="comment-text">{comment.text}</p>
                      </div>
                    ))
                ) : (
                  <p className="no-comments">Пока нет комментариев. Будьте первым!</p>
                )}
              </div>
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

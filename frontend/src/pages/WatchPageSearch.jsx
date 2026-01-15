import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { animeAPI, userAPI } from '../services/api'
import { normalizeAvatarUrl } from '../utils/avatarUtils'
import { parseMentions } from '../utils/parseMentions'
import VideoPlayer from '../components/VideoPlayer'
import AnimeCard from '../components/AnimeCard'
import './WatchPage.css'

function WatchPageSearch() {
  const { animeName } = useParams()
  const navigate = useNavigate()
  const [anime, setAnime] = useState(null)
  const [randomAnime, setRandomAnime] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [authError, setAuthError] = useState(false)
  const [retryAttempted, setRetryAttempted] = useState(false)
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [commentText, setCommentText] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [avatarErrors, setAvatarErrors] = useState({}) // Ошибки загрузки аватарок комментариев
  const [lastCommentTime, setLastCommentTime] = useState(null) // Время последнего комментария
  const [commentCooldown, setCommentCooldown] = useState(0) // Осталось секунд до следующего комментария
  const COMMENT_COOLDOWN_SECONDS = 60 // Время между комментариями в секундах
  const cooldownIntervalRef = useRef(null)

  useEffect(() => {
    if (animeName) {
      // Прокручиваем страницу вверх при переходе на страницу аниме
      window.scrollTo(0, 0)
      setRetryAttempted(false) // Сбрасываем флаг при изменении animeName
      setLastCommentTime(null) // Сбрасываем время последнего комментария
      setCommentCooldown(0) // Сбрасываем кулдаун
      loadAnime()
      loadRandomAnime()
    }
  }, [animeName])

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

  // Обратный отсчет для кулдауна комментариев
  useEffect(() => {
    if (commentCooldown > 0) {
      cooldownIntervalRef.current = setInterval(() => {
        setCommentCooldown((prev) => {
          if (prev <= 1) {
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } else {
      if (cooldownIntervalRef.current) {
        clearInterval(cooldownIntervalRef.current)
        cooldownIntervalRef.current = null
      }
    }

    return () => {
      if (cooldownIntervalRef.current) {
        clearInterval(cooldownIntervalRef.current)
      }
    }
  }, [commentCooldown])

  const loadAnime = async () => {
    try {
      setLoading(true)
      setAuthError(false)
      const response = await animeAPI.getAnimeBySearchName(animeName)
      if (response.message) {
        const animeData = response.message
        // Проверяем, что это объект аниме, а не массив (для совместимости)
        if (Array.isArray(animeData) && animeData.length > 0) {
          // Если пришел массив, берем первый элемент
          const firstAnime = animeData[0]
          if (firstAnime.id && firstAnime.players && firstAnime.players.length > 0) {
            navigate(`/watch/${firstAnime.id}`)
            return
          }
          setAnime(firstAnime)
        } else if (animeData && typeof animeData === 'object' && animeData.id) {
          // Если аниме имеет ID и players, проверяем авторизацию перед показом плеера
          if (animeData.players && animeData.players.length > 0) {
            // Перенаправляем на защищенную страницу просмотра
            navigate(`/watch/${animeData.id}`)
            return
          }
          setAnime(animeData)
        } else {
          // Если ничего не найдено и еще не делали повторный запрос
          if (!retryAttempted) {
            setRetryAttempted(true)
            // Делаем повторный запрос
            try {
              const retryResponse = await animeAPI.getAnimeBySearchName(animeName)
              if (retryResponse.message) {
                const retryAnimeData = retryResponse.message
                if (Array.isArray(retryAnimeData) && retryAnimeData.length > 0) {
                  const firstAnime = retryAnimeData[0]
                  if (firstAnime.id && firstAnime.players && firstAnime.players.length > 0) {
                    navigate(`/watch/${firstAnime.id}`)
                    return
                  }
                  setAnime(firstAnime)
                } else if (retryAnimeData && typeof retryAnimeData === 'object' && retryAnimeData.id) {
                  if (retryAnimeData.players && retryAnimeData.players.length > 0) {
                    navigate(`/watch/${retryAnimeData.id}`)
                    return
                  }
                  setAnime(retryAnimeData)
                } else {
                  setError('Аниме не найдено')
                }
              } else {
                setError('Аниме не найдено')
              }
            } catch (retryErr) {
              console.error('Ошибка повторного запроса:', retryErr)
              setError('Аниме не найдено')
            }
          } else {
            setError('Аниме не найдено')
          }
        }
      } else {
        // Если response.message пустое и еще не делали повторный запрос
        if (!retryAttempted) {
          setRetryAttempted(true)
          try {
            const retryResponse = await animeAPI.getAnimeBySearchName(animeName)
            if (retryResponse.message) {
              const retryAnimeData = retryResponse.message
              if (Array.isArray(retryAnimeData) && retryAnimeData.length > 0) {
                const firstAnime = retryAnimeData[0]
                if (firstAnime.id && firstAnime.players && firstAnime.players.length > 0) {
                  navigate(`/watch/${firstAnime.id}`)
                  return
                }
                setAnime(firstAnime)
              } else if (retryAnimeData && typeof retryAnimeData === 'object' && retryAnimeData.id) {
                if (retryAnimeData.players && retryAnimeData.players.length > 0) {
                  navigate(`/watch/${retryAnimeData.id}`)
                  return
                }
                setAnime(retryAnimeData)
              } else {
                setError('Аниме не найдено')
              }
            } else {
              setError('Аниме не найдено')
            }
          } catch (retryErr) {
            console.error('Ошибка повторного запроса:', retryErr)
            if (retryErr.response?.status === 401) {
              setAuthError(true)
              setError('Для просмотра аниме необходимо войти в аккаунт')
            } else {
              setError('Аниме не найдено')
            }
          }
        } else {
          setError('Аниме не найдено')
        }
      }
      setError(null)
    } catch (err) {
      // Если ошибка и еще не делали повторный запрос
      if (!retryAttempted) {
        setRetryAttempted(true)
        try {
          const retryResponse = await animeAPI.getAnimeBySearchName(animeName)
          if (retryResponse.message) {
            const retryAnimeData = retryResponse.message
            if (Array.isArray(retryAnimeData) && retryAnimeData.length > 0) {
              const firstAnime = retryAnimeData[0]
              if (firstAnime.id && firstAnime.players && firstAnime.players.length > 0) {
                navigate(`/watch/${firstAnime.id}`)
                return
              }
              setAnime(firstAnime)
            } else if (retryAnimeData && typeof retryAnimeData === 'object' && retryAnimeData.id) {
              if (retryAnimeData.players && retryAnimeData.players.length > 0) {
                navigate(`/watch/${retryAnimeData.id}`)
                return
              }
              setAnime(retryAnimeData)
            } else {
              setError('Аниме не найдено')
            }
          } else {
            setError('Аниме не найдено')
          }
        } catch (retryErr) {
          console.error('Ошибка повторного запроса:', retryErr)
          setError('Аниме не найдено')
        }
      } else {
        setError('Аниме не найдено')
        console.error(err)
      }
    } finally {
      setLoading(false)
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

  const handleSubmitComment = async (e) => {
    e.preventDefault()
    if (!commentText.trim() || !anime || commentCooldown > 0) return

    try {
      setSubmittingComment(true)
      await userAPI.createComment(anime.id, commentText)
      setCommentText('')
      // Сохраняем время отправки комментария
      setLastCommentTime(Date.now())
      setCommentCooldown(COMMENT_COOLDOWN_SECONDS)
      // Инвалидируем кэш аниме после создания комментария
      const { invalidateAnimeRelatedCache } = await import('../utils/cache')
      invalidateAnimeRelatedCache()
      // Перезагружаем аниме, чтобы получить обновленные комментарии
      await loadAnime()
    } catch (err) {
      console.error('Ошибка при отправке комментария:', err)
      if (err.response?.status === 429) {
        // Ошибка защиты от спама
        const errorMessage = err.response?.data?.detail || 'Вы отправляете комментарии слишком часто. Подождите немного.'
        alert(errorMessage)
        // Устанавливаем кулдаун из ответа сервера, если возможно
        setLastCommentTime(Date.now())
        setCommentCooldown(COMMENT_COOLDOWN_SECONDS)
      } else {
        alert('Ошибка при отправке комментария')
      }
    } finally {
      setSubmittingComment(false)
    }
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
            <h1 className="anime-title-main">{anime.title}</h1>
            {anime.title_original && (
              <p className="anime-original-title">{anime.title_original}</p>
            )}
            
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
              
              {anime.status && (
                <div className="detail-row">
                  <span className="detail-label">Статус:</span>
                  <span className="detail-value">{anime.status}</span>
                </div>
              )}
              
              {anime.genres && anime.genres.length > 0 && (
                <div className="detail-row">
                  <span className="detail-label">Жанры:</span>
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
              
              {anime.studio && (
                <div className="detail-row">
                  <span className="detail-label">Студия:</span>
                  <Link 
                    to={`/anime/all/anime?studio=${encodeURIComponent(anime.studio)}`}
                    className="detail-value studio-link"
                  >
                    {anime.studio}
                  </Link>
                </div>
              )}
              
              {anime.year && (
                <div className="detail-row">
                  <span className="detail-label">Год:</span>
                  <span className="detail-value">{anime.year}</span>
                </div>
              )}
              
              {anime.type && (
                <div className="detail-row">
                  <span className="detail-label">Тип:</span>
                  <span className="detail-value">{anime.type}</span>
                </div>
              )}
            </div>
            
            {anime.description && (
              <div className="anime-description-section">
                <h3 className="section-title">Обзор</h3>
                <p className="anime-description-text">{anime.description}</p>
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
                  disabled={submittingComment || !commentText.trim() || commentCooldown > 0}
                  className="comment-submit-btn"
                  title={commentCooldown > 0 ? `Подождите ${commentCooldown} секунд перед отправкой следующего комментария` : ''}
                >
                  {submittingComment 
                    ? 'Отправка...' 
                    : commentCooldown > 0 
                    ? `Подождите ${commentCooldown}с`
                    : 'Отправить'}
                </button>
              </form>

              {/* Список комментариев */}
              <div className="comments-list">
                {anime.comments && anime.comments.length > 0 ? (
                  anime.comments.map((comment) => (
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
                                  onError={(e) => {
                                    // Останавливаем повторные попытки загрузки
                                    e.target.src = ''
                                    setAvatarErrors(prev => ({ ...prev, [comment.id]: true }))
                                  }}
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
                          <span className="comment-username">{comment.user?.username || 'User'}</span>
                        </div>
                        <span className="comment-date">{formatDate(comment.created_at)}</span>
                      </div>
                      <p className="comment-text">{parseMentions(comment.text)}</p>
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

export default WatchPageSearch


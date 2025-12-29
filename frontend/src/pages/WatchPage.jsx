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

  useEffect(() => {
    loadAnime()
    loadRandomAnime()
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
    if (!commentText.trim()) return

    try {
      setSubmittingComment(true)
      await userAPI.createComment(parseInt(animeId), commentText)
      setCommentText('')
      // Перезагружаем аниме, чтобы получить обновленные комментарии
      await loadAnime()
    } catch (err) {
      console.error('Ошибка при отправке комментария:', err)
      alert('Ошибка при отправке комментария')
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
            <h1 className="anime-title-main">{anime.title}</h1>
            {anime.title_original && (
              <p className="anime-original-title">{anime.title_original}</p>
            )}
            
            <div className="anime-details-grid">
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
                      <span key={genre.id} className="genre-tag">
                        {genre.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {anime.studio && (
                <div className="detail-row">
                  <span className="detail-label">Студия:</span>
                  <span className="detail-value">{anime.studio}</span>
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
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Оставьте пару слов..."
                  className="comment-input"
                  rows="3"
                />
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
                  anime.comments.map((comment) => (
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
                        <span className="comment-date">{formatDate(comment.created_at)}</span>
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

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { animeAPI } from '../services/api'
import VideoPlayer from '../components/VideoPlayer'
import './WatchPage.css'

function WatchPage() {
  const { animeId } = useParams()
  const [anime, setAnime] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedEpisode, setSelectedEpisode] = useState(1)
  const [selectedPlayer, setSelectedPlayer] = useState(null)

  useEffect(() => {
    loadAnime()
  }, [animeId])

  useEffect(() => {
    if (anime && anime.players && anime.players.length > 0) {
      // Используем первый доступный плеер
      // В структуре данных AnimePlayerModel содержит embed_url
      const player = anime.players[0]
      if (player) {
        setSelectedPlayer({
          ...player,
          player_url: player.embed_url || player.player_url
        })
      }
    }
  }, [anime, selectedEpisode])

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

  const episodes = anime.episodes || []
  const maxEpisode = anime.episodes_count || episodes.length || 1

  return (
    <div className="watch-page">
      <div className="container">
        <div className="watch-header">
          <h1 className="watch-title">{anime.title}</h1>
          {anime.title_original && (
            <p className="watch-original-title">{anime.title_original}</p>
          )}
        </div>

        <div className="watch-content">
          <div className="watch-main">
            <div className="video-container">
              {selectedPlayer ? (
                <VideoPlayer player={selectedPlayer} />
              ) : (
                <div className="no-player">Плеер не доступен</div>
              )}
            </div>

            <div className="episode-selector">
              <h3>Эпизоды</h3>
              <div className="episodes-grid">
                {Array.from({ length: maxEpisode }, (_, i) => i + 1).map((epNum) => (
                  <button
                    key={epNum}
                    className={`episode-btn ${selectedEpisode === epNum ? 'active' : ''}`}
                    onClick={() => setSelectedEpisode(epNum)}
                  >
                    {epNum}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="watch-sidebar">
            <div className="anime-info-card">
              <img
                src={anime.poster_url || '/placeholder.jpg'}
                alt={anime.title}
                className="anime-poster-large"
              />
              
              <div className="anime-details">
                {anime.score && (
                  <div className="detail-item">
                    <span className="detail-label">Рейтинг:</span>
                    <span className="detail-value">★ {anime.score.toFixed(1)}</span>
                  </div>
                )}
                
                {anime.year && (
                  <div className="detail-item">
                    <span className="detail-label">Год:</span>
                    <span className="detail-value">{anime.year}</span>
                  </div>
                )}
                
                {anime.type && (
                  <div className="detail-item">
                    <span className="detail-label">Тип:</span>
                    <span className="detail-value">{anime.type}</span>
                  </div>
                )}
                
                {anime.status && (
                  <div className="detail-item">
                    <span className="detail-label">Статус:</span>
                    <span className="detail-value">{anime.status}</span>
                  </div>
                )}
                
                {anime.studio && (
                  <div className="detail-item">
                    <span className="detail-label">Студия:</span>
                    <span className="detail-value">{anime.studio}</span>
                  </div>
                )}
              </div>

              {anime.description && (
                <div className="anime-description">
                  <h4>Описание</h4>
                  <p>{anime.description}</p>
                </div>
              )}

              {anime.genres && anime.genres.length > 0 && (
                <div className="anime-genres">
                  <h4>Жанры</h4>
                  <div className="genres-list">
                    {anime.genres.map((genre) => (
                      <span key={genre.id} className="genre-tag">
                        {genre.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WatchPage


import { useState } from 'react'
import { Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import './BestAnimeSection.css'

function BestAnimeCard({ anime, place, size, isOwner, onSelect, onRemove }) {
  const posterUrl = anime?.poster_url || '/placeholder.jpg'
  const title = anime?.title || 'Выбрать аниме'
  const score = anime?.score ? parseFloat(anime.score) : null
  const scoreDisplay = score ? score.toFixed(1) : null

  const getScoreClass = (scoreValue) => {
    if (!scoreValue) return ''
    if (scoreValue === 10) return 'score-perfect'
    if (scoreValue >= 7 && scoreValue < 10) return 'score-high'
    if (scoreValue >= 4 && scoreValue < 7) return 'score-medium'
    if (scoreValue >= 1 && scoreValue < 4) return 'score-low'
    return ''
  }

  const scoreClass = getScoreClass(score)

  return (
    <div className={`best-anime-card best-anime-card-${size}`}>
      <div className="best-anime-card-place">#{place}</div>
      {anime ? (
        <>
          {isOwner && (
            <button 
              className="best-anime-card-remove" 
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onRemove(place)
              }}
              title="Удалить"
            >
              ×
            </button>
          )}
          <Link to={`/watch/${anime.id}`} className="best-anime-card-link">
            <div className="best-anime-card-poster">
              <img src={posterUrl} alt={title} loading="lazy" />
              {score && (
                <div className={`best-anime-card-score ${scoreClass}`}>
                  {score === 10 ? <span className="star-icon">🌟</span> : <span>★</span>}
                  {scoreDisplay}
                </div>
              )}
            </div>
            <div className="best-anime-card-info">
              <h3 className="best-anime-card-title">{title}</h3>
            </div>
          </Link>
        </>
      ) : isOwner ? (
        <div className="best-anime-card-empty" onClick={() => onSelect(place)}>
          <div className="best-anime-card-empty-icon">+</div>
          <div className="best-anime-card-empty-text">Выбрать аниме</div>
        </div>
      ) : null}
    </div>
  )
}

function BestAnimeSection({ bestAnime, favorites, isOwner, onUpdate }) {
  const [showModal, setShowModal] = useState(false)
  const [selectedPlace, setSelectedPlace] = useState(null)
  const [loading, setLoading] = useState(false)

  // Создаем массив для 3 позиций
  const animeByPlace = {
    1: bestAnime.find(a => a.place === 1) || null,
    2: bestAnime.find(a => a.place === 2) || null,
    3: bestAnime.find(a => a.place === 3) || null,
  }

  const handleSelect = (place) => {
    setSelectedPlace(place)
    setShowModal(true)
  }

  const handleAnimeSelect = async (animeId) => {
    try {
      setLoading(true)
      await userAPI.setBestAnime(animeId, selectedPlace)
      setShowModal(false)
      setSelectedPlace(null)
      if (onUpdate) {
        onUpdate()
      }
    } catch (error) {
      console.error('Ошибка при установке аниме:', error)
      alert(error.response?.data?.detail || 'Ошибка при установке аниме')
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (place) => {
    if (!window.confirm('Удалить аниме с этого места?')) {
      return
    }
    try {
      setLoading(true)
      await userAPI.removeBestAnime(place)
      if (onUpdate) {
        onUpdate()
      }
    } catch (error) {
      console.error('Ошибка при удалении аниме:', error)
      alert(error.response?.data?.detail || 'Ошибка при удалении аниме')
    } finally {
      setLoading(false)
    }
  }

  // Если пользователь не владелец и нет ни одного аниме, не показываем секцию
  if (!isOwner && bestAnime.length === 0) {
    return null
  }

  const sizes = { 1: 'large', 2: 'medium', 3: 'small' }

  return (
    <div className="best-anime-section">
      <div className="best-anime-section-header">
        <h2 className="best-anime-section-title">Топ-3 аниме</h2>
      </div>
      <div className="best-anime-cards-container">
        {[1, 2, 3].map((place) => {
          // Если пользователь не владелец и карточка пустая, не показываем её
          if (!isOwner && animeByPlace[place] === null) {
            return null
          }
          return (
            <BestAnimeCard
              key={place}
              anime={animeByPlace[place]}
              place={place}
              size={sizes[place]}
              isOwner={isOwner}
              onSelect={handleSelect}
              onRemove={handleRemove}
            />
          )
        })}
      </div>

      {showModal && (
        <div className="best-anime-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="best-anime-modal" onClick={(e) => e.stopPropagation()}>
            <div className="best-anime-modal-header">
              <h3>Выбрать аниме для места #{selectedPlace}</h3>
              <button 
                className="best-anime-modal-close" 
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>
            <div className="best-anime-modal-content">
              {favorites && favorites.length > 0 ? (
                <div className="best-anime-modal-list">
                  {favorites.map((anime) => (
                    <div
                      key={anime.id}
                      className="best-anime-modal-item"
                      onClick={() => handleAnimeSelect(anime.id)}
                    >
                      <img 
                        src={anime.poster_url || '/placeholder.jpg'} 
                        alt={anime.title}
                        className="best-anime-modal-item-poster"
                      />
                      <div className="best-anime-modal-item-info">
                        <div className="best-anime-modal-item-title">{anime.title}</div>
                        {anime.year && (
                          <div className="best-anime-modal-item-year">{anime.year}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="best-anime-modal-empty">
                  У вас нет аниме в избранном
                </div>
              )}
            </div>
            {loading && (
              <div className="best-anime-modal-loading">Загрузка...</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default BestAnimeSection


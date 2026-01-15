import { useState, memo, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { userAPI } from '../services/api'
import LazyImage from './LazyImage'
import './BestAnimeSection.css'
import './LazyImage.css'

const BestAnimeCard = memo(function BestAnimeCard({ anime, place, size, isOwner, onSelect, onRemove, avatarBorderColor }) {
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
    <div 
      className={`best-anime-card best-anime-card-${size}`}
    >
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
              style={avatarBorderColor ? { backgroundColor: avatarBorderColor } : {}}
            >
              ×
            </button>
          )}
          <Link to={`/watch/${anime.id}`} className="best-anime-card-link">
            <div className="best-anime-card-poster">
              <LazyImage 
                src={posterUrl} 
                alt={title} 
                className="lazy-image"
              />
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
})

const BestAnimeSection = memo(function BestAnimeSection({ bestAnime, favorites, isOwner, onUpdate, avatarBorderColor }) {
  const [showModal, setShowModal] = useState(false)
  const [selectedPlace, setSelectedPlace] = useState(null)
  const [loading, setLoading] = useState(false)

  // Создаем массив для 3 позиций с использованием useMemo для правильного обновления
  const animeByPlace = useMemo(() => ({
    1: bestAnime.find(a => a.place === 1) || null,
    2: bestAnime.find(a => a.place === 2) || null,
    3: bestAnime.find(a => a.place === 3) || null,
  }), [bestAnime])


  const handleSelect = (place) => {
    setSelectedPlace(place)
    setShowModal(true)
  }

  const handleAnimeSelect = async (animeId) => {
    // Защита от двойных кликов
    if (loading) {
      return
    }
    try {
      setLoading(true)
      await userAPI.setBestAnime(animeId, selectedPlace)
      setShowModal(false)
      setSelectedPlace(null)
      if (onUpdate) {
        await onUpdate()
      }
    } catch (error) {
      console.error('Ошибка при установке аниме:', error)
      alert(error.response?.data?.detail || 'Ошибка при установке аниме')
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (place) => {
    // Защита от двойных кликов
    if (loading) {
      return
    }
    if (!window.confirm('Удалить аниме с этого места?')) {
      return
    }
    try {
      setLoading(true)
      await userAPI.removeBestAnime(place)
      if (onUpdate) {
        await onUpdate()
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

  // Размеры: карточка 1 - большая, карточка 2 - средняя, карточка 3 - немного меньше карточки 2
  const sizes = { 1: 'large', 2: 'medium-large', 3: 'medium-plus' }
  // Порядок отображения: карточка 2, затем 1, затем 3
  const displayOrder = [2, 1, 3]

  return (
    <div className="best-anime-section">
      <div className="best-anime-section-header">
        <div className="best-anime-section-title-wrapper">
          <div className="sort-info-tooltip">
            <span className="tooltip-icon">?</span>
            <div className="tooltip-content">
              <div>Аниме из этого раздела видны другим пользователям в вашем профиле</div>
              <div className="tooltip-divider"></div>
              <div className="tooltip-secondary-text">Если только что добавленное аниме ещё не отображается — подождите минуту, оно появится.</div>
            </div>
          </div>
          <h2 className="best-anime-section-title">
            Топ-3 аниме
          </h2>
        </div>
      </div>
      <div className="best-anime-cards-container">
        {displayOrder.map((place) => {
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
              avatarBorderColor={avatarBorderColor}
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
})

export default BestAnimeSection


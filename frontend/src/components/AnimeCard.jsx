import { Link } from 'react-router-dom'
import './AnimeCard.css'

function AnimeCard({ anime }) {
  const posterUrl = anime.poster_url || '/placeholder.jpg'
  const title = anime.title || 'Без названия'
  const score = anime.score ? parseFloat(anime.score) : null
  const scoreDisplay = score ? score.toFixed(1) : null
  const year = anime.year || null
  const description = anime.description || ''
  const descriptionShort = description.length > 50 ? description.substring(0, 50) + '...' : description

  // Определяем класс оценки в зависимости от значения
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
    <div className="anime-card-wrapper">
      <Link to={`/watch/${anime.id}`} className="anime-card">
        <div className="anime-card-poster">
          <img src={posterUrl} alt={title} loading="lazy" />
          {score && (
            <div className={`anime-card-score ${scoreClass}`}>
              {score === 10 ? <span className="star-icon">🌟</span> : <span>★</span>}
              {scoreDisplay}
            </div>
          )}
        </div>
        <div className="anime-card-info">
          <h3 className="anime-card-title">{title}</h3>
          {description && (
            <p className="anime-card-description">{descriptionShort}</p>
          )}
          {year && <span className="anime-card-year">{year}</span>}
        </div>
      </Link>
    </div>
  )
}

export default AnimeCard


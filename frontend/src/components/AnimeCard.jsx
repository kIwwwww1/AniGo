import { Link } from 'react-router-dom'
import './AnimeCard.css'

function AnimeCard({ anime }) {
  const posterUrl = anime.poster_url || '/placeholder.jpg'
  const title = anime.title || 'Без названия'
  const score = anime.score ? anime.score.toFixed(1) : null
  const year = anime.year || null

  return (
    <Link to={`/watch/${anime.id}`} className="anime-card">
      <div className="anime-card-poster">
        <img src={posterUrl} alt={title} loading="lazy" />
        {score && (
          <div className="anime-card-score">
            <span>★</span> {score}
          </div>
        )}
      </div>
      <div className="anime-card-info">
        <h3 className="anime-card-title">{title}</h3>
        {year && <span className="anime-card-year">{year}</span>}
      </div>
    </Link>
  )
}

export default AnimeCard


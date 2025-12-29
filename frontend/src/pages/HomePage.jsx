import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { animeAPI } from '../services/api'
import AnimeCard from '../components/AnimeCard'
import './HomePage.css'

function HomePage() {
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [offset, setOffset] = useState(0)
  const limit = 12

  useEffect(() => {
    loadAnime()
  }, [offset])

  const loadAnime = async () => {
    try {
      setLoading(true)
      const response = await animeAPI.getAnimePaginated(limit, offset)
      if (response.message) {
        setAnimeList(response.message)
      }
      setError(null)
    } catch (err) {
      setError('Ошибка загрузки аниме')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    setOffset(prev => prev + limit)
  }

  if (loading && animeList.length === 0) {
    return (
      <div className="home-page">
        <div className="container">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="home-page">
      <div className="container">
        <section className="hero">
          <h2 className="hero-title">Добро пожаловать в AniGo</h2>
          <p className="hero-subtitle">Смотрите лучшие аниме онлайн</p>
        </section>

        <section className="anime-section">
          <h2 className="section-title">Каталог аниме</h2>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="anime-grid">
            {animeList.map((anime) => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>

          {animeList.length > 0 && (
            <div className="load-more-container">
              <button onClick={loadMore} className="load-more-btn" disabled={loading}>
                {loading ? 'Загрузка...' : 'Загрузить еще'}
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default HomePage


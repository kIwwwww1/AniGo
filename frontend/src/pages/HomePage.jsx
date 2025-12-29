import { useState, useEffect } from 'react'
import { animeAPI } from '../services/api'
import AnimeCard from '../components/AnimeCard'
import PopularAnimeCarousel from '../components/PopularAnimeCarousel'
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
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0 || offset === 0) {
        if (offset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
      }
      setError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки аниме'
      setError(errorMessage)
      console.error('Ошибка загрузки аниме:', err)
      console.error('Детали ошибки:', err.response?.data)
      
      // При первой загрузке устанавливаем пустой список
      if (offset === 0) {
        setAnimeList([])
      }
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    setOffset(prev => prev + limit)
  }

  return (
    <div className="home-page">
      <div className="container">
        <section className="hero">
          <h2 className="hero-title">Добро пожаловать в AniGo</h2>
          <p className="hero-subtitle">Смотрите лучшие аниме онлайн</p>
        </section>

        {/* Карусель популярных аниме */}
        <PopularAnimeCarousel />

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


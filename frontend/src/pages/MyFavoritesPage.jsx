import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { userAPI } from '../services/api'
import AnimeGrid from '../components/AnimeGrid'
import '../components/AnimeCardGrid.css'
import './MyFavoritesPage.css'

function MyFavoritesPage() {
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const itemsPerPage = 6

  useEffect(() => {
    loadFavorites()
  }, [])

  const loadFavorites = async () => {
    try {
      setLoading(true)
      const response = await userAPI.getFavorites()
      if (response.message) {
        // Преобразуем избранное в формат аниме
        const animeList = Array.isArray(response.message) 
          ? response.message.map(fav => fav.anime || fav)
          : []
        setFavorites(animeList)
      } else {
        setFavorites([])
      }
      setError(null)
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Необходимо войти в аккаунт для просмотра избранного')
        // Перенаправляем на главную через 2 секунды
        setTimeout(() => {
          navigate('/')
        }, 2000)
      } else {
        setError('Ошибка загрузки избранного')
        console.error('Ошибка загрузки избранного:', err)
      }
      setFavorites([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <div className="error-message">{error}</div>
        </div>
      </div>
    )
  }

  if (favorites.length === 0) {
    return (
      <div className="my-favorites-page">
        <div className="container">
          <section className="popular-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Мои избранные аниме</h2>
                <p className="favorites-count">Всего: 0</p>
              </div>
            </div>
            <div className="empty-favorites">
              <div className="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </div>
              <h3 className="empty-title">У вас пока нет избранных аниме</h3>
              <p className="empty-description">
                Добавьте аниме в избранное, чтобы они отображались здесь
              </p>
            </div>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="my-favorites-page">
      <div className="container">
        <AnimeGrid
          title="Мои избранные аниме"
          animeList={favorites}
          itemsPerPage={itemsPerPage}
          maxPagesToShow={Math.ceil(favorites.length / itemsPerPage)}
          showExpandButton={false}
          showControls={favorites.length > itemsPerPage}
          showIndicators={favorites.length > itemsPerPage}
          emptyMessage="Нет избранных аниме"
          className="popular-anime-section"
        />
      </div>
    </div>
  )
}

export default MyFavoritesPage

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { userAPI } from '../services/api'
import AnimeGrid from '../components/AnimeGrid'
import '../components/AnimeCardGrid.css'
import './UserProfilePage.css'
import '../pages/HomePage.css'

function UserProfilePage() {
  const { username } = useParams()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const itemsPerPage = 6
  const maxPagesToShow = 3

  useEffect(() => {
    loadUserProfile()
  }, [username])

  const loadUserProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await userAPI.getUserProfile(username)
      if (response.message) {
        setUser(response.message)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Пользователь не найден')
      console.error('Ошибка загрузки профиля:', err)
    } finally {
      setLoading(false)
    }
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

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="loading">Загрузка профиля...</div>
        </div>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="user-profile-page">
        <div className="container">
          <div className="error-message">{error || 'Пользователь не найден'}</div>
        </div>
      </div>
    )
  }

  // Преобразуем избранное в формат аниме
  // favorites теперь уже массив объектов аниме, а не массив объектов с полем anime
  const favoritesAnime = user.favorites || []

  // Получаем статистику из ответа API
  const stats = user.stats || {
    favorites_count: favoritesAnime.length,
    ratings_count: 0,
    comments_count: 0,
    watch_history_count: 0,
    unique_watched_anime: 0
  }

  return (
    <div className="user-profile-page">
      <div className="container">
        <div className="profile-header">
          <div className="profile-avatar-section">
            {user.avatar_url ? (
              <img 
                src={user.avatar_url} 
                alt={user.username}
                className="profile-avatar"
              />
            ) : (
              <div className="profile-avatar" style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-secondary)',
                fontSize: '3rem',
                fontWeight: 'bold'
              }}>
                {user.username?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
          </div>
          <div className="profile-info-section">
            <h1 className="profile-username">{user.username}</h1>
            {user.email && <p className="profile-email">{user.email}</p>}
            {user.created_at && (
              <p className="profile-joined">
                Присоединился: {formatDate(user.created_at)}
              </p>
            )}
            {user.role && (
              <span className={`profile-role role-${user.role}`}>
                {user.role === 'admin' ? 'Администратор' : 'Пользователь'}
              </span>
            )}
          </div>
        </div>

        <div className="profile-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.favorites_count}</div>
            <div className="stat-label">Избранное</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.ratings_count}</div>
            <div className="stat-label">Оценок</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.comments_count}</div>
            <div className="stat-label">Комментариев</div>
          </div>
        </div>

        {favoritesAnime.length > 0 ? (
          <AnimeGrid
            title="Избранное"
            animeList={favoritesAnime}
            itemsPerPage={itemsPerPage}
            maxPagesToShow={maxPagesToShow}
            showExpandButton={false}
            showControls={favoritesAnime.length > itemsPerPage}
            showIndicators={favoritesAnime.length > itemsPerPage}
            emptyMessage="Нет избранных аниме"
            className="popular-anime-section"
          />
        ) : (
          <section className="popular-anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Избранное</h2>
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              У пользователя нет избранных аниме
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default UserProfilePage

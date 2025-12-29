import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import './Layout.css'

function Layout({ children }) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Временные данные пользователя (позже будет из контекста/API)
  const user = {
    username: 'Пользователь',
    avatar: 'https://via.placeholder.com/40/333333/ffffff?text=U'
  }

  return (
    <div className="layout">
      <header className={`header ${scrolled ? 'scrolled' : ''}`}>
        <div className="container">
          <div className="header-left">
            <Link to="/" className="logo">
              <h1>AniGo</h1>
            </Link>
            <nav className="nav">
              <Link to="/" className="nav-link">Главная</Link>
              <Link to="/my" className="nav-link">Моё</Link>
              <Link to="/search" className="nav-link search-link">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
              </Link>
            </nav>
          </div>
          <div className="header-right">
            <span className="user-username">{user.username}</span>
            <div className="user-avatar">
              <img src={user.avatar} alt={user.username} />
            </div>
          </div>
        </div>
      </header>
      <main className="main">
        {children}
      </main>
      <footer className="footer">
        <div className="container">
          <p>&copy; 2024 AniGo. Все права защищены.</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout


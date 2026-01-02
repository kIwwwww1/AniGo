import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { userAPI } from '../services/api'
import './Layout.css'

function Layout({ children }) {
  const [scrolled, setScrolled] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  })
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [loginError, setLoginError] = useState('')
  const [registerError, setRegisterError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const [registerLoading, setRegisterLoading] = useState(false)
  const [user, setUser] = useState(null)
  const [loadingUser, setLoadingUser] = useState(true)
  const [showUserDropdown, setShowUserDropdown] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Проверяем авторизацию при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setLoadingUser(true)
        const response = await userAPI.getCurrentUser()
        if (response.message) {
          setUser({
            id: response.message.id,
            username: response.message.username,
            email: response.message.email,
            avatar: response.message.avatar_url || '/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg',
            role: response.message.role
          })
        }
      } catch (err) {
        // Пользователь не авторизован
        setUser(null)
      } finally {
        setLoadingUser(false)
      }
    }
    checkAuth()
  }, [])

  // Закрываем dropdown при клике вне его
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserDropdown && !event.target.closest('.user-menu-container')) {
        setShowUserDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showUserDropdown])

  const handleLogout = async () => {
    try {
      await userAPI.logout()
      setUser(null)
      setShowUserDropdown(false)
    } catch (err) {
      console.error('Ошибка при выходе:', err)
      // Все равно очищаем состояние пользователя
      setUser(null)
      setShowUserDropdown(false)
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    
    if (!loginForm.username || !loginForm.password) {
      setLoginError('Все поля обязательны для заполнения')
      return
    }

    try {
      setLoginLoading(true)
      await userAPI.login(loginForm.username, loginForm.password)
      setShowLoginModal(false)
      setLoginForm({ username: '', password: '' })
      // Небольшая задержка для установки cookie
      await new Promise(resolve => setTimeout(resolve, 500))
      // Проверяем авторизацию после входа
      try {
        const response = await userAPI.getCurrentUser()
        if (response.message) {
          setUser({
            id: response.message.id,
            username: response.message.username,
            email: response.message.email,
            avatar: response.message.avatar_url || '/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg',
            role: response.message.role
          })
        }
      } catch (authErr) {
        // Если не получилось получить пользователя, пробуем еще раз через секунду
        setTimeout(async () => {
          try {
            const response = await userAPI.getCurrentUser()
            if (response.message) {
              setUser({
                id: response.message.id,
                username: response.message.username,
                email: response.message.email,
                avatar: response.message.avatar_url || '/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg',
                role: response.message.role
              })
            }
          } catch (e) {
            console.error('Ошибка проверки авторизации:', e)
          }
        }, 1000)
      }
    } catch (err) {
      setLoginError(err.response?.data?.detail || 'Ошибка при входе')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setRegisterError('')
    
    if (!registerForm.username || !registerForm.email || !registerForm.password) {
      setRegisterError('Все поля обязательны для заполнения')
      return
    }

    if (registerForm.username.length < 3 || registerForm.username.length > 15) {
      setRegisterError('Имя пользователя должно быть от 3 до 15 символов')
      return
    }

    try {
      setRegisterLoading(true)
      await userAPI.createAccount(registerForm.username, registerForm.email, registerForm.password)
      setShowRegisterModal(false)
      setRegisterForm({ username: '', email: '', password: '' })
      // Небольшая задержка для установки cookie
      await new Promise(resolve => setTimeout(resolve, 500))
      // Проверяем авторизацию после регистрации
      try {
        const response = await userAPI.getCurrentUser()
        if (response.message) {
          setUser({
            id: response.message.id,
            username: response.message.username,
            email: response.message.email,
            avatar: response.message.avatar_url || '/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg',
            role: response.message.role
          })
        }
      } catch (authErr) {
        // Если не получилось получить пользователя, пробуем еще раз через секунду
        setTimeout(async () => {
          try {
            const response = await userAPI.getCurrentUser()
            if (response.message) {
              setUser({
                username: response.message.username,
                avatar: response.message.avatar_url || '/Users/kiww1/AniGo/6434d6b8c1419741cb26ec1cd842aca8.jpg'
              })
            }
          } catch (e) {
            console.error('Ошибка проверки авторизации:', e)
          }
        }, 1000)
      }
    } catch (err) {
      setRegisterError(err.response?.data?.detail || 'Ошибка при создании аккаунта')
    } finally {
      setRegisterLoading(false)
    }
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
            {loadingUser ? (
              <div className="user-loading">Загрузка...</div>
            ) : user ? (
              <div className="user-menu-container">
                <span className="user-username">{user.username}</span>
                <div 
                  className="user-avatar"
                  onClick={() => setShowUserDropdown(!showUserDropdown)}
                >
                  <img src={user.avatar} alt={user.username} />
                </div>
                {showUserDropdown && (
                  <div className="user-dropdown">
                    <div className="user-dropdown-header">
                      <div className="dropdown-user-info">
                        <div className="dropdown-avatar">
                          <img src={user.avatar} alt={user.username} />
                        </div>
                        <div className="dropdown-user-details">
                          <div className="dropdown-username">{user.username}</div>
                          <div className="dropdown-email">{user.email}</div>
                        </div>
                      </div>
                    </div>
                    <div className="user-dropdown-menu">
                      <button 
                        className="dropdown-item"
                        onClick={() => {
                          setShowUserDropdown(false)
                          // Можно добавить навигацию на страницу профиля
                          // navigate('/profile')
                          alert('Страница профиля будет реализована позже')
                        }}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <span>Профиль</span>
                      </button>
                      <button 
                        className="dropdown-item logout-item" 
                        onClick={handleLogout}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                          <polyline points="16 17 21 12 16 7"></polyline>
                          <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                        <span>Выйти</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="auth-buttons">
                <button 
                  className="login-btn"
                  onClick={() => setShowLoginModal(true)}
                >
                  Войти
                </button>
                <button 
                  className="register-btn"
                  onClick={() => setShowRegisterModal(true)}
                >
                  Регистрация
                </button>
              </div>
            )}
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

      {/* Модальное окно входа */}
      {showLoginModal && (
        <div className="modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close-btn"
              onClick={() => setShowLoginModal(false)}
              aria-label="Закрыть"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="modal-title">Вход</h2>
            <form onSubmit={handleLogin} className="register-form">
              <div className="form-group">
                <label htmlFor="login-username">Имя пользователя</label>
                <input
                  type="text"
                  id="login-username"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                  placeholder="Введите имя пользователя"
                  minLength={3}
                  maxLength={15}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="login-password">Пароль</label>
                <input
                  type="password"
                  id="login-password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                  placeholder="Введите пароль"
                  required
                />
              </div>
              {loginError && (
                <div className="form-error">{loginError}</div>
              )}
              <button 
                type="submit" 
                className="register-submit-btn"
                disabled={loginLoading}
              >
                {loginLoading ? 'Вход...' : 'Войти'}
              </button>
            </form>
            <div className="modal-footer">
              <p>Нет аккаунта? <button 
                className="link-btn"
                onClick={() => {
                  setShowLoginModal(false)
                  setShowRegisterModal(true)
                }}
              >
                Зарегистрироваться
              </button></p>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно регистрации */}
      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close-btn"
              onClick={() => setShowRegisterModal(false)}
              aria-label="Закрыть"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="modal-title">Регистрация</h2>
            <form onSubmit={handleRegister} className="register-form">
              <div className="form-group">
                <label htmlFor="username">Имя пользователя</label>
                <input
                  type="text"
                  id="username"
                  value={registerForm.username}
                  onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                  placeholder="От 3 до 15 символов"
                  minLength={3}
                  maxLength={15}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                  placeholder="example@email.com"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="password">Пароль</label>
                <input
                  type="password"
                  id="password"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                  placeholder="Введите пароль"
                  required
                />
              </div>
              {registerError && (
                <div className="form-error">{registerError}</div>
              )}
              <button 
                type="submit" 
                className="register-submit-btn"
                disabled={registerLoading}
              >
                {registerLoading ? 'Создание...' : 'Создать аккаунт'}
              </button>
            </form>
            <div className="modal-footer">
              <p>Уже есть аккаунт? <button 
                className="link-btn"
                onClick={() => {
                  setShowRegisterModal(false)
                  setShowLoginModal(true)
                }}
              >
                Войти
              </button></p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Layout


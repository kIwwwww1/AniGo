import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { userAPI, adminAPI } from '../services/api'
import './AdminPanel.css'

function AdminPanel() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentUser, setCurrentUser] = useState(null)
  const [avatarBorderColor, setAvatarBorderColor] = useState('#ff0000')
  const [currentPage, setCurrentPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const usersLimit = 10 // Количество пользователей на странице
  const navigate = useNavigate()

  useEffect(() => {
    checkAdminAccess()
    loadUsers(0)
  }, [])

  useEffect(() => {
    // Загружаем цвет обводки аватара текущего пользователя из API
    const loadAvatarBorderColor = async () => {
      if (currentUser && currentUser.username) {
        try {
          const response = await userAPI.getProfileSettings()
          if (response.message && response.message.avatar_border_color) {
            const savedColor = response.message.avatar_border_color
            setAvatarBorderColor(savedColor)
            // Сохраняем цвет в localStorage для быстрой загрузки при следующем открытии
            localStorage.setItem('user-avatar-border-color', savedColor)
          }
        } catch (err) {
          // Игнорируем ошибки
        }
      }
    }
    loadAvatarBorderColor()
  }, [currentUser])

  const checkAdminAccess = async () => {
    try {
      const response = await userAPI.getCurrentUser()
      if (response && response.message) {
        const userType = response.message.type_account
        if (userType !== 'admin' && userType !== 'owner') {
          navigate('/')
          return
        }
        setCurrentUser(response.message)
      } else {
        navigate('/')
      }
    } catch (err) {
      console.error('Ошибка проверки доступа:', err)
      navigate('/')
    }
  }

  const loadUsers = async (page = 0) => {
    try {
      setLoading(true)
      setError('')
      const offset = page * usersLimit
      const response = await adminAPI.getAllUsers(usersLimit, offset)
      if (response.message) {
        const newUsers = Array.isArray(response.message) ? response.message : []
        
        // Если мы перешли на пустую страницу (не первую), возвращаемся на предыдущую
        if (page > 0 && newUsers.length === 0) {
          await loadUsers(page - 1)
          return
        }
        
        setUsers(newUsers)
        // Следующая страница есть только если мы получили ровно usersLimit пользователей
        setHasMore(newUsers.length === usersLimit)
        setCurrentPage(page)
      }
    } catch (err) {
      console.error('Ошибка загрузки пользователей:', err)
      setError('Не удалось загрузить список пользователей')
    } finally {
      setLoading(false)
    }
  }

  const handleNextPage = async () => {
    if (!loading && hasMore) {
      const nextPage = currentPage + 1
      const offset = nextPage * usersLimit
      try {
        const response = await adminAPI.getAllUsers(usersLimit, offset)
        const nextUsers = Array.isArray(response.message) ? response.message : []
        
        // Если следующая страница пустая, не переходим
        if (nextUsers.length === 0) {
          setHasMore(false)
          return
        }
        
        await loadUsers(nextPage)
      } catch (err) {
        console.error('Ошибка проверки следующей страницы:', err)
      }
    }
  }

  const handlePrevPage = () => {
    if (!loading && currentPage > 0) {
      loadUsers(currentPage - 1)
    }
  }

  const handleBlockUser = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите заблокировать этого пользователя?')) {
      return
    }
    try {
      await adminAPI.blockUser(userId)
      await loadUsers(currentPage)
    } catch (err) {
      console.error('Ошибка блокировки пользователя:', err)
      alert('Не удалось заблокировать пользователя')
    }
  }

  const handleUnblockUser = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите разблокировать этого пользователя?')) {
      return
    }
    try {
      await adminAPI.unblockUser(userId)
      await loadUsers(currentPage)
    } catch (err) {
      console.error('Ошибка разблокировки пользователя:', err)
      alert('Не удалось разблокировать пользователя')
    }
  }

  const handleMakeAdmin = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите назначить этого пользователя администратором?')) {
      return
    }
    try {
      await adminAPI.makeAdmin(userId)
      alert('Пользователь успешно назначен администратором')
      await loadUsers(currentPage)
    } catch (err) {
      console.error('Ошибка назначения администратором:', err)
      const errorMessage = err.response?.data?.detail || 'Не удалось назначить пользователя администратором'
      alert(errorMessage)
    }
  }

  const handleRemoveAdmin = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите снять права администратора у этого пользователя?')) {
      return
    }
    try {
      await adminAPI.removeAdmin(userId)
      alert('Права администратора успешно сняты')
      await loadUsers(currentPage)
    } catch (err) {
      console.error('Ошибка снятия прав администратора:', err)
      const errorMessage = err.response?.data?.detail || 'Не удалось снять права администратора'
      alert(errorMessage)
    }
  }

  const handleDeleteTestData = async () => {
    const confirmMessage = '⚠️ ВНИМАНИЕ!\n\n' +
      'Вы собираетесь удалить ВСЕХ пользователей с типом аккаунта "base" и "admin" и все связанные с ними данные:\n' +
      '- Комментарии\n' +
      '- Избранное\n' +
      '- Рейтинги\n' +
      '- Топ-3 аниме\n' +
      '- Историю просмотров\n\n' +
      'Пользователи с типом "owner" НЕ будут удалены.\n\n' +
      'Это действие НЕОБРАТИМО!\n\n' +
      'Введите "УДАЛИТЬ" для подтверждения:'
    
    const userInput = window.prompt(confirmMessage)
    
    if (userInput !== 'УДАЛИТЬ') {
      return
    }
    
    try {
      setLoading(true)
      const response = await adminAPI.deleteTestData()
      alert(`✅ Успешно удалено:\n` +
        `- Пользователей: ${response.statistics.deleted_users}\n` +
        `- Комментариев: ${response.statistics.deleted_comments}\n` +
        `- Избранного: ${response.statistics.deleted_favorites}\n` +
        `- Рейтингов: ${response.statistics.deleted_ratings}\n` +
        `- Топ-3 аниме: ${response.statistics.deleted_best_anime}\n` +
        `- Истории просмотров: ${response.statistics.deleted_watch_history}`)
      await loadUsers(0)
    } catch (err) {
      console.error('Ошибка удаления тестовых данных:', err)
      alert('Не удалось удалить тестовые данные')
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user => {
    const query = searchQuery.toLowerCase()
    return (
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
    )
  })

  const getAccountTypeLabel = (type) => {
    const labels = {
      'base': 'Обычный',
      'admin': 'Администратор',
      'owner': 'Владелец'
    }
    return labels[type] || type
  }

  const getAccountTypeClass = (type) => {
    const classes = {
      'base': 'account-type-base',
      'admin': 'account-type-admin',
      'owner': 'account-type-owner'
    }
    return classes[type] || ''
  }

  if (loading && !currentUser) {
    return (
      <div className="admin-panel">
        <div className="admin-loading">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="admin-panel" style={{ '--admin-accent-color': avatarBorderColor }}>
      <div className="admin-container">
        <div className="admin-header">
          <h1 style={{ color: avatarBorderColor }}>Админ панель</h1>
          <p className="admin-subtitle">Управление пользователями</p>
        </div>

        {error && (
          <div className="admin-error">{error}</div>
        )}

        <div className="admin-controls">
          <div className="admin-search">
            <input
              type="text"
              placeholder="Поиск пользователей..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="admin-search-input"
            />
          </div>
          <div className="admin-controls-buttons">
            <button 
              className="admin-refresh-btn"
              onClick={() => loadUsers(currentPage)}
              disabled={loading}
            >
              {loading ? 'Загрузка...' : 'Обновить'}
            </button>
            <button 
              className="admin-delete-test-btn"
              onClick={handleDeleteTestData}
              disabled={loading}
            >
              {loading ? 'Удаление...' : 'Удалить тестовые данные'}
            </button>
          </div>
        </div>

        <div className="admin-users-table">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя пользователя</th>
                <th>Email</th>
                <th>Тип аккаунта</th>
                <th>Статус</th>
                <th>Дата регистрации</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="admin-empty">
                    {loading ? 'Загрузка...' : 'Пользователи не найдены'}
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className={user.is_blocked ? 'user-blocked' : ''}>
                    <td>{user.id}</td>
                    <td>
                      <Link 
                        to={`/profile/${user.username}`}
                        className="admin-username-link"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {user.username}
                      </Link>
                    </td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`account-type-badge ${getAccountTypeClass(user.type_account)}`}>
                        {getAccountTypeLabel(user.type_account)}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${user.is_blocked ? 'status-blocked' : 'status-active'}`}>
                        {user.is_blocked ? 'Заблокирован' : 'Активен'}
                      </span>
                    </td>
                    <td>
                      {user.created_at ? new Date(user.created_at).toLocaleDateString('ru-RU') : '-'}
                    </td>
                    <td className="admin-actions">
                      {user.type_account !== 'owner' && (
                        <>
                          {user.is_blocked ? (
                            <button
                              className="admin-btn admin-btn-unblock"
                              onClick={() => handleUnblockUser(user.id)}
                              disabled={loading}
                            >
                              Разблокировать
                            </button>
                          ) : (
                            <button
                              className="admin-btn admin-btn-block"
                              onClick={() => handleBlockUser(user.id)}
                              disabled={loading}
                            >
                              Заблокировать
                            </button>
                          )}
                          {currentUser?.type_account === 'owner' && user.type_account === 'base' && (
                            <button
                              className="admin-btn admin-btn-make-admin"
                              onClick={() => handleMakeAdmin(user.id)}
                              disabled={loading}
                              style={{ marginLeft: '8px' }}
                            >
                              Сделать админом
                            </button>
                          )}
                          {currentUser?.type_account === 'owner' && user.type_account === 'admin' && (
                            <button
                              className="admin-btn admin-btn-remove-admin"
                              onClick={() => handleRemoveAdmin(user.id)}
                              disabled={loading}
                              style={{ marginLeft: '8px' }}
                            >
                              Снять права админа
                            </button>
                          )}
                        </>
                      )}
                      {user.type_account === 'owner' && (
                        <span className="admin-no-action">Недоступно</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Пагинация */}
        {(users.length > 0 || currentPage > 0) && (
          <div className="admin-pagination">
            <button
              type="button"
              className="admin-pagination-btn"
              onClick={handlePrevPage}
              disabled={loading || currentPage === 0}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
              Назад
            </button>
            
            <span className="admin-page-info">
              Страница {currentPage + 1}
            </span>
            
            <button
              type="button"
              className="admin-pagination-btn"
              onClick={handleNextPage}
              disabled={loading || !hasMore}
            >
              Вперед
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPanel


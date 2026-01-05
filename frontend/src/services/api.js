import axios from 'axios'

// В dev режиме всегда используем прокси через Vite (/api)
// В production можно использовать прямой URL через VITE_API_URL
const API_BASE_URL = import.meta.env.MODE === 'production' && import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 секунд таймаут
  withCredentials: true, // Отправлять cookies с запросами
})

// Обработка ошибок сети
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
      console.error('Ошибка сети:', error)
      return Promise.reject({
        ...error,
        isNetworkError: true,
        message: 'Ошибка подключения к серверу'
      })
    }
    // Для 401 ошибок (неавторизован) не логируем ошибку
    if (error.response?.status === 401) {
      return Promise.reject(error)
    }
    return Promise.reject(error)
  }
)

export const animeAPI = {
  // Получить аниме по названию (поиск)
  getAnimeBySearchName: async (name) => {
    const response = await api.get(`/anime/search/${encodeURIComponent(name)}`)
    return response.data
  },

  // Получить аниме по названию (старый метод)
  getAnimeByName: async (name) => {
    const response = await api.get(`/anime/${encodeURIComponent(name)}`)
    return response.data
  },

  // Получить аниме с пагинацией
  getAnimePaginated: async (limit = 12, offset = 0) => {
    const response = await api.get('/anime/get/paginators', {
      params: { limit, offset },
    })
    return response.data
  },

  // Проверить существование аниме
  checkAnimeExists: async (name) => {
    const response = await api.get(`/anime/${encodeURIComponent(name)}/exists`)
    return response.data
  },

  // Получить аниме по ID
  getAnimeById: async (id) => {
    const response = await api.get(`/anime/${id}`)
    return response.data
  },

  // Получить популярные аниме
  getPopularAnime: async (limit = 6, offset = 0) => {
    const response = await api.get('/anime/popular', {
      params: { limit, offset },
    })
    return response.data
  },

  // Получить случайные аниме
  getRandomAnime: async (limit = 3) => {
    const response = await api.get('/anime/random', {
      params: { limit },
    })
    return response.data
  },

  // Получить общее количество аниме
  getAnimeCount: async () => {
    const response = await api.get('/anime/count')
    return response.data
  },

  // Получить все популярные аниме (по 12 штук)
  getAllPopularAnime: async (limit = 12, offset = 0) => {
    const response = await api.get('/anime/all/popular', {
      params: { limit, offset },
    })
    return response.data
  },

  // Получить все аниме (по 12 штук)
  getAllAnime: async (limit = 12, offset = 0) => {
    const response = await api.get('/anime/all/anime', {
      params: { limit, offset },
    })
    return response.data
  },

  // Получить комментарии к аниме с пагинацией
  getCommentsPaginated: async (animeId, limit = 4, offset = 0) => {
    const response = await api.get('/anime/comment/paginator', {
      params: { anime_id: animeId, limit, offset },
    })
    return response.data
  },
}

export const userAPI = {
  // Получить текущего пользователя
  getCurrentUser: async () => {
    const response = await api.get('/user/me')
    return response.data
  },

  // Войти в аккаунт
  login: async (username, password) => {
    const response = await api.post('/user/login', {
      username: username,
      password: password,
    })
    return response.data
  },

  // Создать аккаунт
  createAccount: async (username, email, password) => {
    const response = await api.post('/user/create/account', {
      username: username,
      email: email,
      password: password,
    })
    return response.data
  },

  // Подтвердить email
  verifyEmail: async (token) => {
    const response = await api.get('/user/verify-email', {
      params: { token },
    })
    return response.data
  },

  // Создать комментарий к аниме
  createComment: async (animeId, text) => {
    const response = await api.post('/user/create/comment', {
      anime_id: animeId,
      text: text,
    })
    return response.data
  },

  // Создать рейтинг аниме
  createRating: async (animeId, rating) => {
    const response = await api.post('/user/create/rating', {
      anime_id: animeId,
      rating: rating,
    })
    return response.data
  },

  // Выйти из аккаунта
  logout: async () => {
    const response = await api.post('/user/logout')
    return response.data
  },

  // Добавить/удалить аниме из избранного
  toggleFavorite: async (animeId) => {
    const response = await api.post('/user/toggle/favorite', {
      anime_id: animeId,
    })
    return response.data
  },

  // Проверить, есть ли аниме в избранном
  checkFavorite: async (animeId) => {
    const response = await api.get(`/user/check/favorite/${animeId}`)
    return response.data
  },

  // Получить оценку пользователя для аниме
  checkRating: async (animeId) => {
    const response = await api.get(`/user/check/rating/${animeId}`)
    return response.data
  },

  // Получить все избранные аниме пользователя
  getFavorites: async () => {
    const response = await api.get('/user/favorites')
    return response.data
  },

  // Получить профиль пользователя по username
  getUserProfile: async (username) => {
    const response = await api.get(`/user/profile/${encodeURIComponent(username)}`)
    return response.data
  },

  // Получить настройки пользователя по username
  getUserSettings: async (username) => {
    const response = await api.get(`/user/settings/${encodeURIComponent(username)}`)
    return response.data
  },

  // Изменить имя пользователя
  changeUsername: async (newUsername) => {
    const response = await api.patch('/user/change/name', {
      username: newUsername,
    })
    return response.data
  },

  // Изменить пароль
  changePassword: async (oldPassword, oneNewPassword, twoNewPassword) => {
    const response = await api.patch('/user/change/password', {
      old_password: oldPassword,
      one_new_password: oneNewPassword,
      two_new_password: twoNewPassword,
    })
    return response.data
  },

  // Установить аниме на место в топ-3
  setBestAnime: async (animeId, place) => {
    const response = await api.post('/user/best-anime', {
      anime_id: animeId,
      place: place,
    })
    return response.data
  },

  // Получить топ-3 аниме текущего пользователя
  getBestAnime: async () => {
    const response = await api.get('/user/best-anime')
    return response.data
  },

  // Удалить аниме с места в топ-3
  removeBestAnime: async (place) => {
    const response = await api.delete(`/user/best-anime/${place}`)
    return response.data
  },
}

export default api


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
    return Promise.reject(error)
  }
)

export const animeAPI = {
  // Получить аниме по названию
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
}

export const userAPI = {
  // Создать комментарий к аниме
  createComment: async (animeId, text) => {
    const response = await api.post('/user/create/comment', {
      anime_id: animeId,
      text: text,
    })
    return response.data
  },
}

export default api


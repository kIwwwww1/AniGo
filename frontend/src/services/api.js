import axios from 'axios'

// В dev режиме используем прокси через Vite (/api), в production - прямой URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

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
    const response = await api.get(`/anime/id/${id}`)
    return response.data
  },

  // Получить популярные аниме
  getPopularAnime: async (limit = 6, offset = 0) => {
    const response = await api.get('/anime/popular', {
      params: { limit, offset },
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


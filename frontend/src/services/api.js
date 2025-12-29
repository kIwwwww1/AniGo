import axios from 'axios'

// В dev режиме используем прокси через Vite (/api), в production - прямой URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
}

export default api


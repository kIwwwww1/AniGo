/**
 * Утилита для кэширования данных в localStorage с поддержкой TTL
 */

import { userAPI } from '../services/api'

const CACHE_PREFIX = 'anigo_cache_'

/**
 * Получить данные из кэша
 * @param {string} key - Ключ кэша
 * @returns {object|null} - Кэшированные данные или null, если кэш истек или отсутствует
 */
export const getFromCache = (key) => {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`
    const cachedData = localStorage.getItem(cacheKey)
    
    if (!cachedData) {
      return null
    }
    
    const parsed = JSON.parse(cachedData)
    const now = Date.now()
    
    // Проверяем, не истек ли TTL
    if (parsed.expiresAt && parsed.expiresAt < now) {
      // Кэш истек, удаляем его
      localStorage.removeItem(cacheKey)
      return null
    }
    
    return parsed.data
  } catch (error) {
    console.error('Error reading from cache:', error)
    return null
  }
}

/**
 * Сохранить данные в кэш
 * @param {string} key - Ключ кэша
 * @param {any} data - Данные для сохранения
 * @param {number} ttlSeconds - Время жизни кэша в секундах
 */
export const setToCache = (key, data, ttlSeconds) => {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`
    const expiresAt = Date.now() + (ttlSeconds * 1000)
    
    const cacheData = {
      data,
      expiresAt,
      cachedAt: Date.now()
    }
    
    localStorage.setItem(cacheKey, JSON.stringify(cacheData))
  } catch (error) {
    console.error('Error writing to cache:', error)
    // Если localStorage переполнен, пытаемся очистить старые записи
    if (error.name === 'QuotaExceededError') {
      console.warn('LocalStorage quota exceeded, trying to clean old cache')
      try {
        // Очищаем истекшие кэши
        const keys = Object.keys(localStorage)
        keys.forEach(cacheKey => {
          if (cacheKey.startsWith(CACHE_PREFIX)) {
            try {
              const cachedData = localStorage.getItem(cacheKey)
              if (cachedData) {
                const parsed = JSON.parse(cachedData)
                if (parsed.expiresAt && parsed.expiresAt < Date.now()) {
                  localStorage.removeItem(cacheKey)
                }
              }
            } catch (e) {
              // Игнорируем ошибки при очистке
            }
          }
        })
        // Пробуем снова
        localStorage.setItem(cacheKey, JSON.stringify(cacheData))
      } catch (retryError) {
        console.warn('Failed to save cache even after cleanup')
      }
    }
  }
}

/**
 * Получить данные из кэша по ключу страницы (для пагинации)
 * @param {string} baseKey - Базовый ключ кэша
 * @param {number} page - Номер страницы (0-based)
 * @returns {object|null} - Кэшированные данные или null
 */
export const getPageFromCache = (baseKey, page) => {
  const pageKey = `${baseKey}_page_${page}`
  return getFromCache(pageKey)
}

/**
 * Сохранить данные страницы в кэш
 * @param {string} baseKey - Базовый ключ кэша
 * @param {number} page - Номер страницы (0-based)
 * @param {any} data - Данные для сохранения
 * @param {number} ttlSeconds - Время жизни кэша в секундах
 */
export const setPageToCache = (baseKey, page, data, ttlSeconds) => {
  const pageKey = `${baseKey}_page_${page}`
  setToCache(pageKey, data, ttlSeconds)
}

/**
 * Маппинг коротких алиасов на полные ключи кэша
 * Для удобства использования из консоли браузера
 */
const CACHE_KEY_ALIASES = {
  'catalog': 'anime_catalog',
  'highest_score': 'anime_highest_score',
  'popular': 'anime_popular',
  'top_users': 'top_users_most_favorited'
}

/**
 * Удалить данные из кэша
 * @param {string} key - Ключ кэша (поддерживает алиасы: 'catalog', 'highest_score', 'popular', 'top_users')
 */
export const removeFromCache = (key) => {
  try {
    // Проверяем, есть ли алиас для этого ключа
    const actualKey = CACHE_KEY_ALIASES[key] || key
    const cacheKey = `${CACHE_PREFIX}${actualKey}`
    
    // Проверяем, существует ли такой ключ в localStorage
    const exists = localStorage.getItem(cacheKey) !== null
    
    if (exists) {
      localStorage.removeItem(cacheKey)
      
      // Отправляем событие для автоматической перезагрузки данных
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('cacheRemoved', { 
          detail: { key: actualKey } 
        }))
      }
    }
  } catch (error) {
    console.error('Error removing from cache:', error)
  }
}

/**
 * Очистить кэш профиля пользователя
 * @param {string} username - Имя пользователя
 */
export const clearUserProfileCache = (username) => {
  if (!username) return
  removeFromCache(`user_profile_${username}`)
}

/**
 * Очистить кэш связанный с пользователем (профиль, избранное, топ коллекционеров)
 * Вызывается при изменении данных пользователя
 */
export const invalidateUserRelatedCache = (username) => {
  if (!username) return
  
  // Очищаем кэш профиля
  clearUserProfileCache(username)
  
  // Очищаем кэш топ коллекционеров (может измениться при изменении избранного)
  removeFromCache('most_favorited_users')
  
  // Очищаем кэш избранного пользователя
  removeFromCache(`user_favorites_${username}`)
}

/**
 * Очистить кэш связанный с аниме (каталог, популярные, высшая оценка)
 * Вызывается при изменении данных аниме (комментарии, рейтинги)
 */
export const invalidateAnimeRelatedCache = () => {
  // Очищаем основные кэши аниме
  removeFromCache('anime_catalog')
  removeFromCache('anime_highest_score')
  removeFromCache('anime_popular')
  
  // Очищаем кэши страниц популярных аниме
  const keys = Object.keys(localStorage)
  keys.forEach(key => {
    if (key.startsWith(`${CACHE_PREFIX}anime_popular_page_`)) {
      localStorage.removeItem(key)
    }
  })
}

/**
 * Очистить весь кэш приложения (внутренняя функция)
 */
const clearAllCacheInternal = () => {
  try {
    const keys = Object.keys(localStorage)
    const removedKeys = []
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key)
        // Извлекаем ключ без префикса для события
        const cacheKey = key.replace(CACHE_PREFIX, '')
        removedKeys.push(cacheKey)
      }
    })
    
    // Отправляем событие для каждого удаленного ключа
    if (typeof window !== 'undefined' && removedKeys.length > 0) {
      removedKeys.forEach(key => {
        window.dispatchEvent(new CustomEvent('cacheRemoved', { 
          detail: { key: key } 
        }))
      })
    }
  } catch (error) {
    console.error('Error clearing cache:', error)
    throw error
  }
}

/**
 * Очистить весь кэш приложения (экспортируемая функция)
 * Доступна для использования в компонентах
 */
export const clearAllCache = clearAllCacheInternal

/**
 * Очистить весь кэш приложения с проверкой прав доступа
 * Доступно только для админов и владельцев
 */
export const clearAllCacheAdmin = async () => {
  try {
    // Проверяем права доступа через API
    const response = await userAPI.getCurrentUser()
    
    if (!response || !response.message) {
      console.error('❌ Доступ запрещен: пользователь не авторизован')
      return { success: false, message: 'Пользователь не авторизован' }
    }
    
    const userType = response.message.type_account
    if (userType !== 'admin' && userType !== 'owner') {
      console.error('❌ Доступ запрещен: недостаточно прав. Требуется роль admin или owner')
      return { success: false, message: 'Недостаточно прав. Требуется роль admin или owner' }
    }
    
    // Если права есть - очищаем кэш
    clearAllCacheInternal()
    return { success: true, message: 'Кэш успешно очищен' }
  } catch (error) {
    if (error.response?.status === 401) {
      console.error('❌ Доступ запрещен: пользователь не авторизован')
      return { success: false, message: 'Пользователь не авторизован' }
    }
    console.error('❌ Ошибка при очистке кэша:', error)
    return { success: false, message: `Ошибка: ${error.message || 'Неизвестная ошибка'}` }
  }
}

/**
 * Очистить только кэш приложения (без настроек темы и других данных)
 * Безопасная альтернатива localStorage.clear()
 */
export const clearAppCacheOnly = () => {
  try {
    const keys = Object.keys(localStorage)
    let removedCount = 0
    
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key)
        removedCount++
        // Извлекаем ключ без префикса для события
        const cacheKey = key.replace(CACHE_PREFIX, '')
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('cacheRemoved', { 
            detail: { key: cacheKey } 
          }))
        }
      }
    })
    
    return { success: true, removedCount }
  } catch (error) {
    console.error('Error clearing app cache:', error)
    return { success: false, error: error.message }
  }
}

// Экспорт в window для доступа из консоли браузера
if (typeof window !== 'undefined') {
  window.clearAllCache = clearAllCacheAdmin // Очистить весь кэш (только для админов/владельцев)
  window.removeFromCache = removeFromCache // Удалить конкретный ключ из кэша (поддерживает алиасы)
  window.clearAppCache = clearAppCacheOnly // Очистить только кэш приложения (без настроек темы)
}

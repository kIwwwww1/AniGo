/**
 * Нормализует URL аватарки пользователя
 * @param {string} url - URL аватарки (может быть локальным путем или URL)
 * @returns {string|null} - Нормализованный URL или null
 */
export const normalizeAvatarUrl = (url) => {
  // Проверяем, что url не пустой и не null/undefined
  if (!url || typeof url !== 'string' || url.trim() === '') {
    return null
  }
  
  const trimmedUrl = url.trim()
  
  // Если это уже полный URL (http/https), возвращаем как есть
  if (trimmedUrl.startsWith('http://') || trimmedUrl.startsWith('https://')) {
    return trimmedUrl
  }
  
  // Если это локальный путь к файлу (например, /Users/...), преобразуем в URL через API
  if (trimmedUrl.includes('/Users/') || trimmedUrl.includes('\\')) {
    // Извлекаем имя файла из пути
    const filename = trimmedUrl.split('/').pop() || trimmedUrl.split('\\').pop()
    if (filename && filename.trim() !== '') {
      // Используем API эндпоинт для получения аватарки
      const apiBaseUrl = import.meta.env.MODE === 'production' && import.meta.env.VITE_API_URL
        ? import.meta.env.VITE_API_URL
        : '/api'
      return `${apiBaseUrl}/avatars/${filename}`
    }
    return null
  }
  
  // Если путь начинается с /, это может быть относительный путь
  if (trimmedUrl.startsWith('/')) {
    return trimmedUrl
  }
  
  // В остальных случаях возвращаем как есть (может быть имя файла)
  return trimmedUrl
}

/**
 * Получает инициалы из имени пользователя
 * @param {string} username - Имя пользователя
 * @returns {string} - Инициалы (первые 2 буквы имени)
 */
export const getInitials = (username) => {
  if (!username) {
    return '??'
  }
  
  // Берем первые 2 буквы имени пользователя
  return username.substring(0, 2).toUpperCase()
}

/**
 * Генерирует цвет на основе имени пользователя
 * @param {string} username - Имя пользователя
 * @returns {string} - HEX цвет
 */
export const getColorFromUsername = (username) => {
  if (!username) {
    return '#888888'
  }
  
  // Список цветов для аватаров
  const colors = [
    '#e50914', // red
    '#ff6b6b', // coral
    '#4ecdc4', // teal
    '#45b7d1', // blue
    '#96ceb4', // mint
    '#ffeaa7', // yellow
    '#dfe6e9', // light gray
    '#a29bfe', // purple
    '#fd79a8', // pink
    '#fdcb6e', // orange
    '#6c5ce7', // violet
    '#00b894', // green
  ]
  
  // Генерируем хеш из имени пользователя
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // Получаем индекс цвета
  const index = Math.abs(hash) % colors.length
  
  return colors[index]
}

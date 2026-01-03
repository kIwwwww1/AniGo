/**
 * Нормализует URL аватарки пользователя
 * @param {string} url - URL аватарки (может быть локальным путем или URL)
 * @returns {string|null} - Нормализованный URL или null
 */
export const normalizeAvatarUrl = (url) => {
  if (!url) {
    return null
  }
  
  // Если это уже полный URL (http/https), возвращаем как есть
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // Если это локальный путь к файлу (например, /Users/...), преобразуем в URL через API
  if (url.includes('/Users/') || url.includes('\\')) {
    // Извлекаем имя файла из пути
    const filename = url.split('/').pop() || url.split('\\').pop()
    if (filename) {
      // Используем API эндпоинт для получения аватарки
      const apiBaseUrl = import.meta.env.MODE === 'production' && import.meta.env.VITE_API_URL
        ? import.meta.env.VITE_API_URL
        : '/api'
      return `${apiBaseUrl}/avatars/${filename}`
    }
    return null
  }
  
  // Если путь начинается с /, это может быть относительный путь
  if (url.startsWith('/')) {
    return url
  }
  
  return url
}


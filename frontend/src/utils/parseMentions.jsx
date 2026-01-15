import React from 'react'
import { Link } from 'react-router-dom'

/**
 * Парсит текст комментария и преобразует @mentions в кликабельные ссылки
 * @param {string} text - Текст комментария
 * @returns {Array|string} - Массив React элементов (текст и ссылки) или строка
 */
export const parseMentions = (text) => {
  if (!text) return null
  
  // Регулярное выражение для поиска @mentions
  // Ищет @ за которым следует имя пользователя (буквы, цифры, подчеркивания, дефисы)
  // Используем [\w-]+ чтобы поддерживать дефисы в именах пользователей
  const mentionRegex = /@([\w-]+)/g
  const parts = []
  let lastIndex = 0
  let match
  let partIndex = 0
  
  while ((match = mentionRegex.exec(text)) !== null) {
    // Добавляем текст до упоминания
    if (match.index > lastIndex) {
      const textPart = text.substring(lastIndex, match.index)
      if (textPart) {
        parts.push(
          <span key={`text-${partIndex++}`}>{textPart}</span>
        )
      }
    }
    
    // Добавляем ссылку на упоминание
    const username = match[1]
    parts.push(
      <Link
        key={`mention-${partIndex++}`}
        to={`/profile/${username}`}
        className="comment-mention"
        onClick={(e) => {
          // Предотвращаем всплытие события, если нужно
          e.stopPropagation()
        }}
      >
        @{username}
      </Link>
    )
    
    lastIndex = mentionRegex.lastIndex
  }
  
  // Добавляем оставшийся текст после последнего упоминания
  if (lastIndex < text.length) {
    const textPart = text.substring(lastIndex)
    if (textPart) {
      parts.push(
        <span key={`text-${partIndex++}`}>{textPart}</span>
      )
    }
  }
  
  // Если упоминаний не было, возвращаем просто текст в массиве для консистентности
  if (parts.length === 0) {
    return <>{text}</>
  }
  
  // Возвращаем Fragment с элементами (React может рендерить массивы напрямую)
  return <>{parts}</>
}

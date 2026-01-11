import { useEffect, useRef, useCallback, useState } from 'react'

/**
 * Hook для debounce функций
 * @param callback - функция для выполнения
 * @param delay - задержка в миллисекундах (по умолчанию 300ms)
 */
export function useDebounce(callback, delay = 300) {
  const timeoutRef = useRef(null)

  const debouncedCallback = useCallback(
    (...args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args)
      }, delay)
    },
    [callback, delay]
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

/**
 * Hook для debounce значений
 * @param value - значение для debounce
 * @param delay - задержка в миллисекундах (по умолчанию 300ms)
 */
export function useDebouncedValue(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

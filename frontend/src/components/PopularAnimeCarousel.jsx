import { useState, useEffect, memo, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { animeAPI } from '../services/api'
import { getFromCache, setToCache, removeFromCache, getPageFromCache, setPageToCache } from '../utils/cache'
import AnimeGrid from './AnimeGrid'
import './PopularAnimeCarousel.css'

const PopularAnimeCarousel = memo(function PopularAnimeCarousel() {
  const navigate = useNavigate()
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const itemsPerPage = 6
  const maxPagesToShow = 3
  const cacheLimit = 18 // Кэшируем 3 страницы по 6 элементов = 18 элементов
  const CACHE_TTL = 300 // Время жизни кэша: 5 минут (300 секунд) - синхронизировано с бэкендом
  const CACHE_KEY_POPULAR = 'anime_popular'
  const loadingPagesRef = useRef(new Set()) // Отслеживаем загружаемые страницы

  // Функция для создания серых плашек-заполнителей
  const createSkeletonCards = (count) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `skeleton-${i}`,
      title: '',
      poster_url: null,
      score: null,
      isPlaceholder: true,
      isSkeleton: true
    }))
  }

  const loadAnimeCount = async () => {
    try {
      const response = await animeAPI.getAnimeCount()
      const count = response.message || 0
      setTotalCount(count)
    } catch (err) {
      console.error('Ошибка загрузки количества популярных аниме:', err)
      setTotalCount(0)
    }
  }

  const loadAnime = useCallback(async (offset, silent = false) => {
    const page = Math.floor(offset / itemsPerPage)
    
    // Проверяем, не загружается ли уже эта страница
    if (loadingPagesRef.current.has(page)) {
      return
    }
    
    try {
      if (!silent) {
        setLoading(true)
      }
      setHasError(false)
      loadingPagesRef.current.add(page)
      
      // Проверяем кэш для конкретной страницы
      const cachedPageData = getPageFromCache(CACHE_KEY_POPULAR, page)
      if (cachedPageData && Array.isArray(cachedPageData)) {
        setAnimeList(prev => {
          const newList = [...prev]
          const startIndex = page * itemsPerPage
          // Если данных еще нет для этой позиции, добавляем в конец
          if (newList.length <= startIndex) {
            return [...newList, ...cachedPageData]
          }
          // Если данные уже есть, обновляем их
          cachedPageData.forEach((item, index) => {
            if (startIndex + index < newList.length) {
              newList[startIndex + index] = item
            } else {
              newList.push(item)
            }
          })
          return newList
        })
        loadingPagesRef.current.delete(page)
        if (!silent) {
          setLoading(false)
        }
        return
      }
      
      // Для первой загрузки проверяем старый формат кэша
      if (offset === 0) {
        const cachedData = getFromCache(CACHE_KEY_POPULAR)
        if (cachedData && Array.isArray(cachedData)) {
          setAnimeList(cachedData)
          // Конвертируем старый формат кэша в новый (постраничный)
          for (let i = 0; i < Math.ceil(cachedData.length / itemsPerPage); i++) {
            const pageData = cachedData.slice(i * itemsPerPage, (i + 1) * itemsPerPage)
            setPageToCache(CACHE_KEY_POPULAR, i, pageData, CACHE_TTL)
          }
          setHasMore(cachedData.length >= cacheLimit)
          setHasError(false)
          loadingPagesRef.current.delete(page)
          if (!silent) {
            setLoading(false)
          }
          return
        }
      }
      
      // Для первой загрузки загружаем cacheLimit элементов (3 страницы)
      const loadLimit = offset === 0 ? cacheLimit : itemsPerPage
      const response = await animeAPI.getPopularAnime(loadLimit, offset)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (offset === 0) {
          setAnimeList(animeData)
          // Сохраняем в кэш по страницам
          for (let i = 0; i < Math.ceil(animeData.length / itemsPerPage); i++) {
            const pageData = animeData.slice(i * itemsPerPage, (i + 1) * itemsPerPage)
            setPageToCache(CACHE_KEY_POPULAR, i, pageData, CACHE_TTL)
          }
          // Также сохраняем старый формат для обратной совместимости
          const dataToCache = animeData.slice(0, cacheLimit)
          setToCache(CACHE_KEY_POPULAR, dataToCache, CACHE_TTL)
        } else {
          // Правильно добавляем данные в конец массива
          // Это работает, потому что AnimeGrid использует индексы для доступа к данным
          setAnimeList(prev => {
            // Если данных еще нет для этой позиции, просто добавляем в конец
            if (prev.length <= offset) {
              return [...prev, ...animeData]
            }
            // Если данные уже есть, обновляем их
            const newList = [...prev]
            animeData.forEach((item, index) => {
              if (offset + index < newList.length) {
                newList[offset + index] = item
              } else {
                newList.push(item)
              }
            })
            return newList
          })
          // Сохраняем страницу в кэш
          setPageToCache(CACHE_KEY_POPULAR, page, animeData, CACHE_TTL)
        }
        setHasMore(animeData.length === loadLimit)
      } else {
        if (offset === 0) {
          setAnimeList(createSkeletonCards(itemsPerPage))
        }
        setHasMore(false)
      }
    } catch (err) {
      console.error('Ошибка загрузки популярных аниме:', err)
      setHasError(true)
      setHasMore(false)
      if (offset === 0 && !silent) {
        setAnimeList(createSkeletonCards(itemsPerPage))
      }
    } finally {
      loadingPagesRef.current.delete(page)
      if (!silent) {
        setLoading(false)
      }
    }
  }, [itemsPerPage, cacheLimit, CACHE_TTL])

  // Сохраняем ссылку на функцию для использования в интервале
  const loadAnimeRef = useRef(loadAnime)

  useEffect(() => {
    loadAnimeRef.current = loadAnime
  }, [loadAnime])

  useEffect(() => {
    loadAnimeCount()
    loadAnime(0)
  }, [loadAnime])

  // Эффект для автоматического обновления данных
  useEffect(() => {
    const interval = setInterval(() => {
      // Принудительно удаляем кэш и обновляем данные для популярных аниме
      removeFromCache(CACHE_KEY_POPULAR)
      // Очищаем постраничный кэш
      for (let i = 0; i < 10; i++) {
        removeFromCache(`${CACHE_KEY_POPULAR}_page_${i}`)
      }
      loadAnimeRef.current(0)
    }, CACHE_TTL * 1000)

    return () => {
      clearInterval(interval)
    }
  }, [CACHE_TTL])
  
  // Предзагрузка второй страницы после загрузки первой
  useEffect(() => {
    if (animeList.length >= itemsPerPage && animeList.length < cacheLimit && hasMore && !loading) {
      // Предзагружаем следующую страницу в фоне
      const nextOffset = itemsPerPage
      loadAnime(nextOffset, true).catch(() => {
        // Игнорируем ошибки при предзагрузке
      })
    }
  }, [animeList.length, itemsPerPage, cacheLimit, hasMore, loading, loadAnime])

  const handleExpand = useCallback(() => {
    // Переходим на страницу со всеми популярными аниме
    navigate('/anime/all/popular')
  }, [navigate])

  const handlePageChange = useCallback((page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    // Проверяем, что данных действительно нет для этой страницы
    const pageStartIndex = page * itemsPerPage
    const pageEndIndex = (page + 1) * itemsPerPage
    const hasDataForPage = animeList.length >= pageEndIndex
    
    if (!hasDataForPage && hasMore) {
      // Загружаем данные для этой страницы
      loadAnime(offset, false).catch((err) => {
        console.error('Ошибка загрузки данных для страницы:', page, err)
      })
    }
    
    // Предзагружаем следующую страницу в фоне
    const nextPage = page + 1
    const nextOffset = nextPage * itemsPerPage
    const nextPageEndIndex = (nextPage + 1) * itemsPerPage
    const hasDataForNextPage = animeList.length >= nextPageEndIndex
    
    if (!hasDataForNextPage && hasMore && nextPage < maxPagesToShow) {
      // Предзагружаем тихо (без показа loading)
      loadAnime(nextOffset, true).catch(() => {
        // Игнорируем ошибки при предзагрузке
      })
    }
  }, [animeList.length, hasMore, loadAnime, itemsPerPage, maxPagesToShow])

  // Определяем, нужно ли показывать серые плашки-заполнители
  // Показываем skeleton если: загрузка идет или аниме нет
  // Если аниме мало (меньше itemsPerPage), показываем реальные аниме + skeleton для заполнения
  // Когда появляется достаточно аниме (>= itemsPerPage), skeleton исчезают
  const shouldShowOnlySkeletons = loading || animeList.length === 0
  
  // Формируем список для отображения - передаем реальный animeList, а не displayList
  // AnimeGrid сам обработает skeleton на основе totalCount
  const totalPages = totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(animeList.length / itemsPerPage)
  const hasMorePages = totalCount > 0 && totalPages > maxPagesToShow && !showAll

  return (
    <AnimeGrid
      title="Популярное аниме"
      animeList={animeList}
      itemsPerPage={itemsPerPage}
      maxPagesToShow={maxPagesToShow}
      showExpandButton={hasMorePages && !shouldShowOnlySkeletons}
      showControls={!shouldShowOnlySkeletons}
      showIndicators={!shouldShowOnlySkeletons}
      totalCount={totalCount}
      emptyMessage="Нет популярных аниме"
      onExpand={handleExpand}
      onPageChange={handlePageChange}
      sortCriteria="Аниме отсортированы по популярности на основе количества просмотров и запросов за последние 2 недели"
    />
  )
})

export default PopularAnimeCarousel

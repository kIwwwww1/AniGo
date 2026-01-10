import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { animeAPI } from '../services/api'
import AnimeGrid from './AnimeGrid'
import './PopularAnimeCarousel.css'

function PopularAnimeCarousel() {
  const navigate = useNavigate()
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const itemsPerPage = 6
  const maxPagesToShow = 3

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

  useEffect(() => {
    loadAnimeCount()
    loadAnime(0)
  }, [])

  const loadAnimeCount = async () => {
    try {
      const response = await animeAPI.getAnimeCount()
      const count = response.message || 0
      setTotalCount(count)
      console.log('PopularAnimeCarousel: totalCount загружен:', count)
    } catch (err) {
      console.error('Ошибка загрузки количества популярных аниме:', err)
      setTotalCount(0)
    }
  }

  const loadAnime = async (offset) => {
    try {
      setLoading(true)
      setHasError(false)
      
      console.log(`Загрузка популярных аниме: limit=${itemsPerPage}, offset=${offset}`)
      
      const response = await animeAPI.getPopularAnime(itemsPerPage, offset)
      
      console.log('Ответ от API:', response)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      console.log(`Получено аниме: ${animeData.length}`)
      
      if (animeData.length > 0) {
        if (offset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === itemsPerPage)
      } else {
        // Если данных нет, показываем серые плашки-заполнители
        console.log('Данных нет, показываем серые плашки-заполнители')
        if (offset === 0) {
          setAnimeList(createSkeletonCards(itemsPerPage))
        }
        setHasMore(false)
      }
    } catch (err) {
      console.error('Ошибка загрузки популярных аниме:', err)
      console.error('Тип ошибки:', err.isNetworkError ? 'Network Error' : 'API Error')
      console.error('Детали ошибки:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        url: err.config?.url
      })
      setHasError(true)
      setHasMore(false)
      // При ошибке показываем серые плашки-заполнители
      if (offset === 0) {
        setAnimeList(createSkeletonCards(itemsPerPage))
      }
    } finally {
      setLoading(false)
    }
  }

  const handleExpand = () => {
    // Переходим на страницу со всеми популярными аниме
    navigate('/anime/all/popular')
  }

  const handlePageChange = (page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    if (offset >= animeList.length && hasMore) {
      loadAnime(offset)
    }
  }

  // Определяем, нужно ли показывать серые плашки-заполнители
  // Показываем skeleton если: загрузка идет или аниме нет
  // Если аниме мало (меньше itemsPerPage), показываем реальные аниме + skeleton для заполнения
  // Когда появляется достаточно аниме (>= itemsPerPage), skeleton исчезают
  const shouldShowOnlySkeletons = loading || animeList.length === 0
  const shouldShowSkeletons = shouldShowOnlySkeletons || (animeList.length > 0 && animeList.length < itemsPerPage)
  
  // Формируем список для отображения
  let displayList = animeList
  if (shouldShowOnlySkeletons) {
    // Если загрузка или нет аниме - показываем только skeleton
    displayList = createSkeletonCards(itemsPerPage)
  } else if (animeList.length > 0 && animeList.length < itemsPerPage) {
    // Если аниме мало - показываем реальные аниме + skeleton для заполнения
    const skeletonCount = itemsPerPage - animeList.length
    displayList = [...animeList, ...createSkeletonCards(skeletonCount)]
  }
  
  const totalPages = totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(displayList.length / itemsPerPage)
  const hasMorePages = totalCount > 0 && totalPages > maxPagesToShow && !showAll

  // Для отладки
  console.log('PopularAnimeCarousel render:', {
    loading,
    animeListLength: animeList.length,
    displayListLength: displayList.length,
    itemsPerPage,
    hasMore,
    shouldShowSkeletons,
    totalCount,
    hasMorePages,
    totalPages: totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(displayList.length / itemsPerPage),
    firstItemIsSkeleton: displayList[0]?.isSkeleton
  })

  return (
    <AnimeGrid
      title="Популярное аниме"
      animeList={displayList}
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
}

export default PopularAnimeCarousel

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

  // Функция для создания пустых карточек
  const createEmptyCards = (count) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `empty-${i}`,
      title: 'Не определено',
      poster_url: null,
      score: null,
      isPlaceholder: true
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
        // Если данных нет, показываем пустые карточки
        console.log('Данных нет, показываем пустые карточки')
        if (offset === 0) {
          setAnimeList(createEmptyCards(itemsPerPage))
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
      // При ошибке показываем пустые карточки
      if (offset === 0) {
        setAnimeList(createEmptyCards(itemsPerPage))
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

  // Всегда показываем секцию, даже если данных нет
  const displayList = animeList.length > 0 ? animeList : createEmptyCards(itemsPerPage)
  const totalPages = totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(displayList.length / itemsPerPage)
  const hasMorePages = totalCount > 0 && totalPages > maxPagesToShow && !showAll

  if (loading && animeList.length === 0) {
    return (
      <section className="anime-card-grid-section">
        <div className="section-header">
          <div className="section-title-wrapper">
            <h2 className="section-title">Популярное аниме</h2>
          </div>
        </div>
        <div className="loading">Загрузка...</div>
      </section>
    )
  }

  // Для отладки
  console.log('PopularAnimeCarousel render:', {
    animeListLength: animeList.length,
    displayListLength: displayList.length,
    totalCount,
    hasMorePages,
    totalPages: totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : Math.ceil(displayList.length / itemsPerPage)
  })

  return (
    <AnimeGrid
      title="Популярное аниме"
      animeList={displayList}
      itemsPerPage={itemsPerPage}
      maxPagesToShow={maxPagesToShow}
      showExpandButton={hasMorePages}
      showControls={true}
      showIndicators={true}
      totalCount={totalCount}
      emptyMessage="Нет популярных аниме"
      onExpand={handleExpand}
      onPageChange={handlePageChange}
    />
  )
}

export default PopularAnimeCarousel

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { animeAPI } from '../services/api'
import PopularAnimeCarousel from '../components/PopularAnimeCarousel'
import AnimeGrid from '../components/AnimeGrid'
import '../components/AnimeCardGrid.css'
import './HomePage.css'

function HomePage() {
  const navigate = useNavigate()
  const [animeList, setAnimeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [showAll, setShowAll] = useState(false)
  
  // Состояние для блока "Высшая оценка"
  const [highestScoreAnime, setHighestScoreAnime] = useState([])
  const [highestScoreLoading, setHighestScoreLoading] = useState(true)
  const [highestScoreError, setHighestScoreError] = useState(null)
  const [highestScoreHasMore, setHighestScoreHasMore] = useState(true)
  
  const limit = 12
  const limitHighestScore = 18 // Для блока "Высшая оценка" загружаем 18 элементов (3 страницы)
  const itemsPerPage = 6
  const maxPagesToShow = 3

  useEffect(() => {
    loadAnimeCount()
    loadAnime(0)
    loadHighestScoreAnime(0)
  }, [])

  const loadAnimeCount = async () => {
    try {
      const response = await animeAPI.getAnimeCount()
      const count = response.message || 0
      setTotalCount(count)
    } catch (err) {
      console.error('Ошибка загрузки количества аниме:', err)
      setTotalCount(0)
    }
  }

  const loadAnime = async (loadOffset) => {
    try {
      setLoading(true)
      const response = await animeAPI.getAnimePaginated(limit, loadOffset)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (loadOffset === 0) {
          setAnimeList(animeData)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === limit)
      } else {
        setHasMore(false)
        if (loadOffset === 0) {
          setAnimeList([])
        }
      }
      setError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки аниме'
      setError(errorMessage)
      console.error('Ошибка загрузки аниме:', err)
      console.error('Детали ошибки:', err.response?.data)
      
      // При первой загрузке устанавливаем пустой список
      if (loadOffset === 0) {
        setAnimeList([])
      }
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }

  const handleExpand = () => {
    // Переходим на страницу со всеми аниме
    navigate('/anime/all/anime')
  }

  const handlePageChange = (page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    if (offset >= animeList.length && hasMore) {
      const loadOffset = Math.floor(animeList.length / limit) * limit
      loadAnime(loadOffset)
    }
  }

  const loadHighestScoreAnime = async (loadOffset) => {
    try {
      setHighestScoreLoading(true)
      const response = await animeAPI.getHighestScoreAnime(limitHighestScore, loadOffset, 'desc')
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (loadOffset === 0) {
          setHighestScoreAnime(animeData)
        } else {
          setHighestScoreAnime(prev => [...prev, ...animeData])
        }
        setHighestScoreHasMore(animeData.length === limitHighestScore)
      } else {
        setHighestScoreHasMore(false)
        if (loadOffset === 0) {
          setHighestScoreAnime([])
        }
      }
      setHighestScoreError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки аниме'
      setHighestScoreError(errorMessage)
      console.error('Ошибка загрузки аниме с высшей оценкой:', err)
      
      if (loadOffset === 0) {
        setHighestScoreAnime([])
      }
      setHighestScoreHasMore(false)
    } finally {
      setHighestScoreLoading(false)
    }
  }

  const handleHighestScoreExpand = () => {
    // Переходим на страницу со всеми аниме
    navigate('/anime/all/anime')
  }

  const handleHighestScorePageChange = (page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    if (offset >= highestScoreAnime.length && highestScoreHasMore) {
      const loadOffset = Math.floor(highestScoreAnime.length / limitHighestScore) * limitHighestScore
      loadHighestScoreAnime(loadOffset)
    }
  }

  // Используем totalCount для правильного вычисления страниц
  const effectiveTotal = totalCount > 0 ? totalCount : animeList.length
  const totalPages = Math.ceil(effectiveTotal / itemsPerPage)
  const displayPages = showAll ? totalPages : Math.min(maxPagesToShow, totalPages)
  const hasMorePages = totalCount > 0 && totalPages > maxPagesToShow && !showAll

  return (
    <div className="home-page">
      <div className="container">
        <section className="hero">
          <h2 className="hero-title">Добро пожаловать в AniGo</h2>
          <p className="hero-subtitle">Смотрите лучшие аниме онлайн</p>
        </section>

        {/* Карусель популярных аниме */}
        <PopularAnimeCarousel />

        {/* Каталог аниме */}
        {error && <div className="error-message">{error}</div>}
        
        {loading && animeList.length === 0 ? (
          <section className="anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Каталог аниме</h2>
              </div>
            </div>
            <div className="loading">Загрузка...</div>
          </section>
        ) : (
          <AnimeGrid
            title="Каталог аниме"
            animeList={animeList}
            itemsPerPage={itemsPerPage}
            maxPagesToShow={maxPagesToShow}
            showExpandButton={hasMorePages}
            showControls={true}
            showIndicators={displayPages > 1}
            totalCount={totalCount}
            emptyMessage="Нет аниме в каталоге"
            onExpand={handleExpand}
            onPageChange={handlePageChange}
            className="anime-section"
            sortCriteria="Все аниме из каталога без специальной сортировки"
          />
        )}

        {/* Блок "Высшая оценка" */}
        {highestScoreError && <div className="error-message">{highestScoreError}</div>}
        
        {highestScoreLoading && highestScoreAnime.length === 0 ? (
          <section className="anime-section">
            <div className="section-header">
              <div className="section-title-wrapper">
                <h2 className="section-title">Высшая оценка</h2>
              </div>
            </div>
            <div className="loading">Загрузка...</div>
          </section>
        ) : (
          highestScoreAnime.length > 0 && (
            <AnimeGrid
              title="Высшая оценка"
              animeList={highestScoreAnime}
              itemsPerPage={itemsPerPage}
              maxPagesToShow={maxPagesToShow}
              showExpandButton={highestScoreHasMore}
              showControls={true}
              showIndicators={Math.ceil(highestScoreAnime.length / itemsPerPage) > 1}
              totalCount={highestScoreAnime.length}
              emptyMessage="Нет аниме с высшей оценкой"
              onExpand={handleHighestScoreExpand}
              onPageChange={handleHighestScorePageChange}
              className="anime-section"
              sortCriteria="Аниме отсортированы по оценке от высокой к низкой"
            />
          )
        )}
      </div>
    </div>
  )
}

export default HomePage

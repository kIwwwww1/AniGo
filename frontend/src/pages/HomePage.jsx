import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { animeAPI } from '../services/api'
import PopularAnimeCarousel from '../components/PopularAnimeCarousel'
import TopUsersSection from '../components/TopUsersSection'
import AnimeGrid from '../components/AnimeGrid'
import QRModal from '../components/QRModal'
import { getFromCache, setToCache, removeFromCache } from '../utils/cache'
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
  
  // Состояние для смены фонового изображения
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const backgroundImages = useMemo(() => ['/screensaver_1.png', '/screensaver_2.png'], [])
  
  // Состояние для модального окна с QR кодом
  const [isQRModalOpen, setIsQRModalOpen] = useState(false)
  
  // Состояние для 3D эффекта параллакса
  const [parallaxStyle, setParallaxStyle] = useState({
    transform: 'translate(0px, 0px) scale(1.1)',
    transition: 'transform 0.5s ease-out'
  })
  const [textParallaxStyle, setTextParallaxStyle] = useState({
    transform: 'translate(0px, 0px)',
    transition: 'transform 0.5s ease-out'
  })
  
  const limit = 12
  const limitHighestScore = 18 // Для блока "Высшая оценка" загружаем 18 элементов (3 страницы)
  const itemsPerPage = 6
  const maxPagesToShow = 3
  const cacheLimit = 18 // Кэшируем 3 страницы по 6 элементов = 18 элементов
  const CACHE_TTL = 300 // Время жизни кэша: 5 минут (300 секунд) - синхронизировано с backend
  const CACHE_KEY_CATALOG = 'anime_catalog'
  const CACHE_KEY_HIGHEST_SCORE = 'anime_highest_score'

  const loadAnimeCount = useCallback(async () => {
    try {
      const response = await animeAPI.getAnimeCount()
      const count = response.message || 0
      setTotalCount(count)
    } catch (err) {
      console.error('Ошибка загрузки количества аниме:', err)
      setTotalCount(0)
    }
  }, [])

  const loadAnime = useCallback(async (loadOffset) => {
    try {
      setLoading(true)
      
      // Для первой загрузки проверяем кэш
      if (loadOffset === 0) {
        const cachedData = getFromCache(CACHE_KEY_CATALOG)
        if (cachedData && Array.isArray(cachedData)) {
          setAnimeList(cachedData)
          setHasMore(cachedData.length >= cacheLimit)
          setError(null)
          setLoading(false)
          return
        }
      }
      
      // Если кэша нет или не первая загрузка, загружаем данные
      // Для первой загрузки загружаем cacheLimit элементов (3 страницы)
      const loadLimit = loadOffset === 0 ? cacheLimit : limit
      const response = await animeAPI.getAnimePaginated(loadLimit, loadOffset)
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (loadOffset === 0) {
          setAnimeList(animeData)
          // Сохраняем в кэш только первые 3 страницы (18 элементов)
          const dataToCache = animeData.slice(0, cacheLimit)
          setToCache(CACHE_KEY_CATALOG, dataToCache, CACHE_TTL)
        } else {
          setAnimeList(prev => [...prev, ...animeData])
        }
        setHasMore(animeData.length === loadLimit)
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
  }, [limit, cacheLimit, CACHE_TTL])

  const loadHighestScoreAnime = useCallback(async (loadOffset) => {
    try {
      setHighestScoreLoading(true)
      
      // Для первой загрузки проверяем кэш
      if (loadOffset === 0) {
        const cachedData = getFromCache(CACHE_KEY_HIGHEST_SCORE)
        if (cachedData && Array.isArray(cachedData)) {
          setHighestScoreAnime(cachedData)
          setHighestScoreHasMore(cachedData.length >= cacheLimit)
          setHighestScoreError(null)
          setHighestScoreLoading(false)
          return
        }
      }
      
      // Если кэша нет или не первая загрузка, загружаем данные
      const response = await animeAPI.getHighestScoreAnime(limitHighestScore, loadOffset, 'desc')
      
      // Обрабатываем ответ - может быть массив или объект с message
      const animeData = Array.isArray(response.message) 
        ? response.message 
        : (response.message || [])
      
      if (animeData.length > 0) {
        if (loadOffset === 0) {
          setHighestScoreAnime(animeData)
          // Сохраняем в кэш только первые 3 страницы (18 элементов)
          const dataToCache = animeData.slice(0, cacheLimit)
          setToCache(CACHE_KEY_HIGHEST_SCORE, dataToCache, CACHE_TTL)
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
  }, [limitHighestScore, cacheLimit, CACHE_TTL])

  const handleExpand = useCallback(() => {
    // Переходим на страницу со всеми аниме
    navigate('/anime/all/anime')
  }, [navigate])

  const handlePageChange = useCallback((page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    if (offset >= animeList.length && hasMore) {
      const loadOffset = Math.floor(animeList.length / limit) * limit
      loadAnime(loadOffset)
    }
  }, [animeList.length, hasMore, limit, loadAnime])

  const handleHighestScoreExpand = useCallback(() => {
    // Переходим на страницу со всеми аниме
    navigate('/anime/all/anime')
  }, [navigate])

  const handleHighestScorePageChange = useCallback((page, offset) => {
    // Загружаем данные для страницы, если их еще нет
    if (offset >= highestScoreAnime.length && highestScoreHasMore) {
      const loadOffset = Math.floor(highestScoreAnime.length / limitHighestScore) * limitHighestScore
      loadHighestScoreAnime(loadOffset)
    }
  }, [highestScoreAnime.length, highestScoreHasMore, limitHighestScore, loadHighestScoreAnime])

  // Функция для обработки движения мыши и создания эффекта параллакса
  const handleMouseMove = useCallback((e) => {
    const banner = e.currentTarget
    const rect = banner.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    
    // Вычисляем смещение в процентах от центра (-1 до 1)
    const percentX = (x - centerX) / centerX
    const percentY = (y - centerY) / centerY
    
    // Смещение фона (больше движение)
    const moveX = percentX * 30 // Максимум 30px
    const moveY = percentY * 30
    
    // Смещение текста (меньше и в противоположную сторону для глубины)
    const textMoveX = percentX * -15 // Максимум 15px в обратную сторону
    const textMoveY = percentY * -15
    
    setParallaxStyle({
      transform: `translate(${moveX}px, ${moveY}px) scale(1.1)`,
      transition: 'transform 0.1s ease-out'
    })
    
    setTextParallaxStyle({
      transform: `translate(${textMoveX}px, ${textMoveY}px)`,
      transition: 'transform 0.1s ease-out'
    })
  }, [])

  const handleMouseLeave = useCallback(() => {
    setParallaxStyle({
      transform: 'translate(0px, 0px) scale(1.1)',
      transition: 'transform 0.5s ease-out'
    })
    
    setTextParallaxStyle({
      transform: 'translate(0px, 0px)',
      transition: 'transform 0.5s ease-out'
    })
  }, [])

  // Сохраняем ссылки на функции для использования в интервале
  const loadAnimeRef = useRef(loadAnime)
  const loadHighestScoreAnimeRef = useRef(loadHighestScoreAnime)

  useEffect(() => {
    loadAnimeRef.current = loadAnime
    loadHighestScoreAnimeRef.current = loadHighestScoreAnime
  }, [loadAnime, loadHighestScoreAnime])

  useEffect(() => {
    loadAnimeCount()
    loadAnime(0)
    loadHighestScoreAnime(0)
  }, [loadAnimeCount, loadAnime, loadHighestScoreAnime])

  // Эффект для автоматического обновления данных каждые 5 минут
  useEffect(() => {
    const interval = setInterval(() => {
      // Принудительно удаляем кэш и обновляем данные для каталога аниме
      removeFromCache(CACHE_KEY_CATALOG)
      loadAnimeRef.current(0)
      
      // Принудительно удаляем кэш и обновляем данные для блока "Высшая оценка"
      removeFromCache(CACHE_KEY_HIGHEST_SCORE)
      loadHighestScoreAnimeRef.current(0)
    }, CACHE_TTL * 1000) // Обновляем каждые 5 минут (300 секунд) - синхронизировано с backend

    return () => {
      clearInterval(interval)
    }
  }, [CACHE_TTL])

  // Эффект для смены фонового изображения каждые 10 секунд
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prevIndex) => (prevIndex + 1) % backgroundImages.length)
    }, 30000) // 30 секунд

    return () => clearInterval(interval)
  }, [backgroundImages.length])

  // Используем totalCount для правильного вычисления страниц
  const effectiveTotal = useMemo(() => 
    totalCount > 0 ? totalCount : animeList.length, 
    [totalCount, animeList.length]
  )
  
  const totalPages = useMemo(() => 
    Math.ceil(effectiveTotal / itemsPerPage), 
    [effectiveTotal, itemsPerPage]
  )
  
  const displayPages = useMemo(() => 
    showAll ? totalPages : Math.min(maxPagesToShow, totalPages), 
    [showAll, totalPages, maxPagesToShow]
  )
  
  const hasMorePages = useMemo(() => 
    totalCount > 0 && totalPages > maxPagesToShow && !showAll, 
    [totalCount, totalPages, maxPagesToShow, showAll]
  )

  return (
    <div className="home-page">
      <section 
        className="hero-banner"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {backgroundImages.map((image, index) => (
          <div
            key={image}
            className={`hero-banner-bg ${index === currentImageIndex ? 'active' : 'inactive'}`}
            style={{ 
              backgroundImage: `url(${image})`,
              ...(index === currentImageIndex ? parallaxStyle : {})
            }}
          />
        ))}
        <div className="hero-overlay" style={textParallaxStyle}>
          <h2 className="hero-title">Добро пожаловать в Yumivo</h2>
          <p className="hero-subtitle">Yumivo — аниме, которое хочется смотреть</p>
        </div>
        <button 
          className="support-button"
          onClick={() => setIsQRModalOpen(true)}
        >
          Поддержать Yumivo
        </button>
      </section>
      
      <QRModal 
        isOpen={isQRModalOpen} 
        onClose={() => setIsQRModalOpen(false)} 
      />

      <div className="container">

        {/* Карусель популярных аниме */}
        <PopularAnimeCarousel />

        {/* Топ коллекционеров */}
        <TopUsersSection />

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

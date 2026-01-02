import { useState, useRef, useEffect } from 'react'
import './VideoPlayer.css'

function VideoPlayer({ player }) {
  const videoRef = useRef(null)
  const containerRef = useRef(null)
  const progressRef = useRef(null)
  const volumeRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [hideControlsTimeout, setHideControlsTimeout] = useState(null)

  // Проверяем, является ли URL прямым видео URL или iframe
  // Все URL от Kodik - это iframe embed URLs, поэтому кастомный HTML5 плеер используется только для прямых видео файлов
  // Для Kodik используется стилизованный iframe контейнер (функциональные контролы невозможны из-за политики безопасности)
  const isDirectVideo = player?.embed_url && (
    player.embed_url.endsWith('.mp4') ||
    player.embed_url.endsWith('.webm') ||
    player.embed_url.endsWith('.ogg') ||
    player.embed_url.endsWith('.m3u8') ||
    player.embed_url.endsWith('.mov') ||
    player.embed_url.startsWith('blob:')
  )

  useEffect(() => {
    const video = videoRef.current
    if (!video || !isDirectVideo) return

    const updateTime = () => setCurrentTime(video.currentTime)
    const updateDuration = () => setDuration(video.duration)
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleEnded = () => setIsPlaying(false)

    video.addEventListener('timeupdate', updateTime)
    video.addEventListener('loadedmetadata', updateDuration)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)
    video.addEventListener('ended', handleEnded)

    video.volume = isMuted ? 0 : volume

    return () => {
      video.removeEventListener('timeupdate', updateTime)
      video.removeEventListener('loadedmetadata', updateDuration)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
      video.removeEventListener('ended', handleEnded)
    }
  }, [isDirectVideo, volume, isMuted])

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return
    if (isPlaying) {
      video.pause()
    } else {
      video.play()
    }
  }

  const handleProgressClick = (e) => {
    const video = videoRef.current
    const progressBar = progressRef.current
    if (!video || !progressBar) return

    const rect = progressBar.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    video.currentTime = percent * duration
  }

  const handleVolumeClick = (e) => {
    const volumeBar = volumeRef.current
    if (!volumeBar) return

    const rect = volumeBar.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    const newVolume = Math.max(0, Math.min(1, percent))
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const toggleMute = () => {
    if (isMuted) {
      setIsMuted(false)
      setVolume(volume || 0.5)
    } else {
      setIsMuted(true)
    }
  }

  const toggleFullscreen = () => {
    if (!containerRef.current) return
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  }

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00'
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleMouseMove = () => {
    setShowControls(true)
    if (hideControlsTimeout) {
      clearTimeout(hideControlsTimeout)
    }
    const timeout = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false)
      }
    }, 3000)
    setHideControlsTimeout(timeout)
  }

  if (!player || !player.embed_url) {
    return (
      <div className="video-player-container">
        <div className="no-video">Видео не доступно</div>
      </div>
    )
  }

  // Если это не прямой видео URL, используем iframe (для Kodik)
  // Применяем стили контейнера в стиле YouTube (круглые края)
  if (!isDirectVideo) {
    return (
      <div 
        className="video-player-container kodik-iframe-wrapper"
        ref={containerRef}
      >
        <div className="video-player-iframe-wrapper">
          <iframe
            src={player.embed_url}
            className="video-iframe"
            allowFullScreen
            sandbox="allow-scripts allow-same-origin allow-popups allow-presentation"
            title="Video Player"
          />
        </div>
      </div>
    )
  }

  return (
    <div 
      className="video-player-container"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => {
        if (isPlaying) {
          const timeout = setTimeout(() => setShowControls(false), 1000)
          setHideControlsTimeout(timeout)
        }
      }}
    >
      <video
        ref={videoRef}
        src={player.embed_url}
        className="custom-video-player"
        onClick={togglePlay}
      />

      <div className={`video-controls ${showControls ? 'visible' : ''}`}>
        {/* Прогресс бар */}
        <div 
          className="progress-container"
          ref={progressRef}
          onClick={handleProgressClick}
        >
          <div 
            className="progress-bar"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
          <div 
            className="progress-handle"
            style={{ left: `${(currentTime / duration) * 100}%` }}
          />
        </div>

        {/* Нижняя панель контролов */}
        <div className="controls-bar">
          <div className="controls-left">
            <button 
              className="control-btn play-pause-btn"
              onClick={togglePlay}
              aria-label={isPlaying ? 'Пауза' : 'Воспроизведение'}
            >
              {isPlaying ? (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              )}
            </button>

            {/* Контроль громкости */}
            <div className="volume-control">
              <button 
                className="control-btn volume-btn"
                onClick={toggleMute}
                aria-label={isMuted ? 'Включить звук' : 'Выключить звук'}
              >
                {isMuted || volume === 0 ? (
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                  </svg>
                ) : volume < 0.5 ? (
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                  </svg>
                )}
              </button>
              <div 
                className="volume-slider"
                ref={volumeRef}
                onClick={handleVolumeClick}
              >
                <div 
                  className="volume-bar"
                  style={{ width: `${(isMuted ? 0 : volume) * 100}%` }}
                />
              </div>
            </div>

            {/* Время */}
            <div className="time-display">
              <span>{formatTime(currentTime)}</span>
              <span> / </span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          <div className="controls-right">
            <button 
              className="control-btn fullscreen-btn"
              onClick={toggleFullscreen}
              aria-label={isFullscreen ? 'Выход из полноэкранного режима' : 'Полноэкранный режим'}
            >
              {isFullscreen ? (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VideoPlayer

import { useEffect, useRef } from 'react'
import './VideoPlayer.css'

function VideoPlayer({ player }) {
  const iframeRef = useRef(null)

  useEffect(() => {
    // Используем embed_url или player_url из AnimePlayerModel
    const videoUrl = player.embed_url || player.player_url || ''
    
    if (iframeRef.current && videoUrl) {
      iframeRef.current.src = videoUrl
    }
  }, [player])

  if (!player || (!player.embed_url && !player.player_url)) {
    return (
      <div className="video-player">
        <div className="no-video">Видео не доступно</div>
      </div>
    )
  }

  return (
    <div className="video-player">
      <iframe
        ref={iframeRef}
        className="video-iframe"
        allowFullScreen
        sandbox="allow-scripts allow-same-origin allow-popups allow-presentation"
        title="Video Player"
      />
    </div>
  )
}

export default VideoPlayer


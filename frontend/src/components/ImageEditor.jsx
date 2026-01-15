import { useState, useRef, useEffect } from 'react'
import './ImageEditor.css'

function ImageEditor({ imageFile, onConfirm, onCancel }) {
  const [imageUrl, setImageUrl] = useState(null)
  const [scale, setScale] = useState(100)
  const [positionX, setPositionX] = useState(50)
  const [positionY, setPositionY] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const previewRef = useRef(null)

  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile)
      setImageUrl(url)
      return () => URL.revokeObjectURL(url)
    }
  }, [imageFile])

  const handleMouseDown = (e) => {
    if (e.target.classList.contains('image-editor-preview-image')) {
      setIsDragging(true)
      setDragStart({
        x: e.clientX - (positionX * previewRef.current.offsetWidth / 100),
        y: e.clientY - (positionY * previewRef.current.offsetHeight / 100)
      })
    }
  }

  const handleMouseMove = (e) => {
    if (isDragging && previewRef.current) {
      const rect = previewRef.current.getBoundingClientRect()
      const newX = ((e.clientX - dragStart.x) / rect.width) * 100
      const newY = ((e.clientY - dragStart.y) / rect.height) * 100
      
      setPositionX(Math.max(0, Math.min(100, newX)))
      setPositionY(Math.max(0, Math.min(100, newY)))
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragStart])

  const handleConfirm = () => {
    onConfirm({
      file: imageFile,
      settings: {
        scale,
        positionX,
        positionY
      }
    })
  }

  const handleReset = () => {
    setScale(100)
    setPositionX(50)
    setPositionY(50)
  }

  return (
    <div className="image-editor-overlay">
      <div className="image-editor-modal">
        <div className="image-editor-header">
          <h2>Настройка фонового изображения</h2>
          <button 
            className="image-editor-close-btn" 
            onClick={onCancel}
            aria-label="Закрыть"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="image-editor-content">
          <div className="image-editor-preview-container">
            <div 
              ref={previewRef}
              className="image-editor-preview"
              onMouseDown={handleMouseDown}
            >
              {imageUrl && (
                <div
                  className="image-editor-preview-image"
                  style={{
                    backgroundImage: `url(${imageUrl})`,
                    backgroundSize: `${scale}%`,
                    backgroundPosition: `${positionX}% ${positionY}%`,
                    cursor: isDragging ? 'grabbing' : 'grab'
                  }}
                />
              )}
            </div>
            <p className="image-editor-hint">
              Перетащите изображение мышью для изменения позиции
            </p>
          </div>

          <div className="image-editor-controls">
            <div className="image-editor-control-group">
              <label htmlFor="scale-slider">
                Масштаб: {scale}%
              </label>
              <input
                id="scale-slider"
                type="range"
                min="50"
                max="200"
                value={scale}
                onChange={(e) => setScale(Number(e.target.value))}
                className="image-editor-slider"
              />
            </div>

            <div className="image-editor-control-group">
              <label htmlFor="position-x-slider">
                Позиция X: {positionX.toFixed(0)}%
              </label>
              <input
                id="position-x-slider"
                type="range"
                min="0"
                max="100"
                value={positionX}
                onChange={(e) => setPositionX(Number(e.target.value))}
                className="image-editor-slider"
              />
            </div>

            <div className="image-editor-control-group">
              <label htmlFor="position-y-slider">
                Позиция Y: {positionY.toFixed(0)}%
              </label>
              <input
                id="position-y-slider"
                type="range"
                min="0"
                max="100"
                value={positionY}
                onChange={(e) => setPositionY(Number(e.target.value))}
                className="image-editor-slider"
              />
            </div>

            <div className="image-editor-buttons">
              <button 
                className="image-editor-reset-btn"
                onClick={handleReset}
              >
                Сбросить
              </button>
              <button 
                className="image-editor-cancel-btn"
                onClick={onCancel}
              >
                Отмена
              </button>
              <button 
                className="image-editor-confirm-btn"
                onClick={handleConfirm}
              >
                Применить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ImageEditor

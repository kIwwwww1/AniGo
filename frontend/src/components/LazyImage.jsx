import { useState, useEffect, useRef, memo } from 'react'

const LazyImage = memo(function LazyImage({ 
  src, 
  alt, 
  className = '', 
  placeholder = '/placeholder.jpg',
  onLoad,
  ...props 
}) {
  const [imageSrc, setImageSrc] = useState(placeholder)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef(null)

  useEffect(() => {
    if (!imgRef.current) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.unobserve(entry.target)
          }
        })
      },
      {
        rootMargin: '50px', // Начинаем загрузку за 50px до попадания в viewport
        threshold: 0.01,
      }
    )

    observer.observe(imgRef.current)

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (isInView && src && src !== placeholder) {
      const img = new Image()
      img.src = src
      img.onload = () => {
        setImageSrc(src)
        setIsLoaded(true)
        if (onLoad) onLoad()
      }
      img.onerror = () => {
        setImageSrc(placeholder)
        setIsLoaded(true)
      }
    }
  }, [isInView, src, placeholder, onLoad])

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={`${className} ${isLoaded ? 'loaded' : 'loading'}`}
      {...props}
    />
  )
})

export default LazyImage

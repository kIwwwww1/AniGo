import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './QRModal.css'

function QRModal({ isOpen, onClose }) {
  const [copied, setCopied] = useState(false)
  const navigate = useNavigate()
  const codeText = 'UQBUDK-Qd0mudliZ-c6XWRmUd9pdg_zX9nRS1ljxTWSSHopL'

  useEffect(() => {
    if (isOpen) {
      // Блокируем прокрутку фона при открытом модальном окне
      document.body.style.overflow = 'hidden'
    } else {
      // Восстанавливаем прокрутку при закрытии
      document.body.style.overflow = ''
    }

    // Очистка при размонтировании компонента
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeText)
      setCopied(true)
      setTimeout(() => {
        setCopied(false)
      }, 2000)
    } catch (err) {
      // Fallback для старых браузеров
      const textArea = document.createElement('textarea')
      textArea.value = codeText
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        setCopied(true)
        setTimeout(() => {
          setCopied(false)
        }, 2000)
      } catch (err) {
        console.error('Ошибка копирования:', err)
      }
      document.body.removeChild(textArea)
    }
  }

  return (
    <div className="qr-modal-overlay" onClick={handleOverlayClick}>
      <div className="qr-modal-content">
        <div className="qr-modal-image-container">
          <img 
            src="/qr2.png" 
            alt="QR код"
            className="qr-modal-image"
          />
        </div>
        <div className="qr-modal-code-container" onClick={handleCopy}>
          <span className="qr-modal-code-text">{codeText}</span>
          <svg 
            className="qr-modal-chain-icon" 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
          >
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
          </svg>
          {copied && <span className="qr-modal-copied">Скопировано!</span>}
        </div>
        <div className="qr-modal-or-divider">
          <span className="qr-modal-or-text">или</span>
        </div>
        <button 
          className="qr-modal-buy-btn"
          onClick={() => {
            onClose()
            navigate('/premium/purchase')
          }}
        >
          Купить
          <img src="/main_korona.png" alt="Корона" className="qr-modal-crown-icon" />
        </button>
      </div>
    </div>
  )
}

export default QRModal

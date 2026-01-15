import { useState } from 'react'
import QRModal from '../components/QRModal'
import './AnimeMerchPage.css'

function PremiumPurchasePremiumPage() {
  const [isQRModalOpen, setIsQRModalOpen] = useState(false)

  return (
    <div className="anime-merch-page">
      <div className="anime-merch-container">
        <img 
          src="/anime-merch.png" 
          alt="Premium" 
          className="anime-merch-image"
        />
        <h2 className="anime-merch-404">404 - Not Found</h2>
        <p className="anime-merch-message">Раздел с «Premium» еще в разработке</p>
        <button 
          className="anime-merch-button"
          onClick={() => setIsQRModalOpen(true)}
        >
          Ускорить разработку
        </button>
      </div>
      <QRModal 
        isOpen={isQRModalOpen} 
        onClose={() => setIsQRModalOpen(false)} 
      />
    </div>
  )
}

export default PremiumPurchasePremiumPage

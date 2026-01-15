import { useNavigate } from 'react-router-dom'
import './PremiumPurchasePage.css'

function PremiumPurchasePage() {
  const navigate = useNavigate()

  const handlePlanSelect = () => {
    navigate('/premium/purchase-premium')
  }

  return (
    <div className="premium-purchase-page">
      <div className="premium-purchase-container">
        <h1 className="premium-purchase-title">Выберите план Premium</h1>
        
        <div className="premium-plans-wrapper">
          {/* Левая плашка */}
          <div className="premium-plan-card premium-plan-left">
            <div className="premium-plan-header">
              <h2 className="premium-plan-name">Месячный план Pro</h2>
              <div className="premium-plan-badge">Популярный</div>
            </div>
            <div className="premium-plan-price">
              <span className="premium-plan-amount">99</span>
              <span className="premium-plan-currency">₽</span>
              <span className="premium-plan-period">/месяц</span>
            </div>
            <ul className="premium-plan-features">
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Доступ ко всем аниме
              </li>
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Приоритетная поддержка
              </li>
              <li className="premium-plan-feature premium-plan-feature-with-sublist">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <div className="premium-plan-feature-content">
                  <span>Кастомизация профиля:</span>
                  <ul className="premium-plan-feature-sublist">
                    <li>смена обложки</li>
                    <li>золотой никнейм</li>
                    <li>корона рядом с именем</li>
                  </ul>
                </div>
              </li>
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Ускорить появление 1080p
              </li>
              <li className="premium-plan-feature-divider"></li>
              <li className="premium-plan-feature premium-plan-feature-with-sublist">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="premium-plan-feature-icon-gray">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <div className="premium-plan-feature-content">
                  <span>Создавайте контент: <span className="premium-plan-feature-soon">(Совсем скоро...)</span></span>
                  <ul className="premium-plan-feature-sublist">
                    <li>
                      Публиковать смешные моменты и эдиты
                      <span className="premium-plan-feature-description"> (делитесь забавными клипами и авторскими видео из аниме)</span>
                    </li>
                    <li>
                      Создавать собственные аниме-викторины
                      <span className="premium-plan-feature-description"> (тестируйте знания других пользователей или придумывайте тематические квизы)</span>
                    </li>
                    <li>
                      Делать персональные подборки аниме
                      <span className="premium-plan-feature-description"> (составляйте списки любимых тайтлов, которые увидят все пользователи)</span>
                    </li>
                    <li>
                      Читать цитаты из аниме
                      <span className="premium-plan-feature-description"> (открывайте вдохновляющие, драматичные или мемные фразы из ваших любимых сериалов)</span>
                    </li>
                  </ul>
                </div>
              </li>
            </ul>
            <button 
              className="premium-plan-button premium-plan-button-left"
              onClick={handlePlanSelect}
            >
              Выбрать план
            </button>
          </div>

          {/* Правая плашка */}
          <div className="premium-plan-card premium-plan-right">
            <div className="premium-plan-header">
              <h2 className="premium-plan-name">Месячный план Pro +</h2>
              <div className="premium-plan-badge premium-plan-badge-best">Выгодно</div>
            </div>
            <div className="premium-plan-price-wrapper">
              <div className="premium-plan-price">
                <span className="premium-plan-amount">999</span>
                <span className="premium-plan-currency">₽</span>
                <span className="premium-plan-period">/год</span>
              </div>
            </div>
            <div className="premium-plan-savings">
              В среднем 83₽/месяц
            </div>
            <div className="premium-plan-special-offer">
              <div className="premium-plan-special-icon">🎫</div>
              <div className="premium-plan-special-text">
                <strong>Первые пять покупателей</strong> получат премиум-доступ навсегда и уникальный бейдж <strong>"Золотой билет"</strong> — он будет только у вас!
              </div>
            </div>
            <ul className="premium-plan-features">
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Доступ ко всем аниме
              </li>
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Приоритетная поддержка
              </li>
              <li className="premium-plan-feature premium-plan-feature-with-sublist">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <div className="premium-plan-feature-content">
                  <span>Кастомизация профиля:</span>
                  <ul className="premium-plan-feature-sublist">
                    <li>смена обложки</li>
                    <li>золотой никнейм</li>
                    <li>корона рядом с именем</li>
                  </ul>
                </div>
              </li>
              <li className="premium-plan-feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Ускорить появление 1080p
              </li>
              <li className="premium-plan-feature-divider"></li>
              <li className="premium-plan-feature premium-plan-feature-with-sublist">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="premium-plan-feature-icon-gray">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <div className="premium-plan-feature-content">
                  <span>Создавайте контент: <span className="premium-plan-feature-soon">(Совсем скоро...)</span></span>
                  <ul className="premium-plan-feature-sublist">
                    <li>
                      Публиковать смешные моменты и эдиты
                      <span className="premium-plan-feature-description"> (делитесь забавными клипами и авторскими видео из аниме)</span>
                    </li>
                    <li>
                      Создавать собственные аниме-викторины
                      <span className="premium-plan-feature-description"> (тестируйте знания других пользователей или придумывайте тематические квизы)</span>
                    </li>
                    <li>
                      Делать персональные подборки аниме
                      <span className="premium-plan-feature-description"> (составляйте списки любимых тайтлов, которые увидят все пользователи)</span>
                    </li>
                    <li>
                      Читать цитаты из аниме
                      <span className="premium-plan-feature-description"> (открывайте вдохновляющие, драматичные или мемные фразы из ваших любимых сериалов)</span>
                    </li>
                  </ul>
                </div>
              </li>
              <li className="premium-plan-feature premium-plan-feature-exclusive">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Эксклюзивный бэйдж
              </li>
            </ul>
            <button 
              className="premium-plan-button premium-plan-button-right"
              onClick={handlePlanSelect}
            >
              Выбрать план
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PremiumPurchasePage

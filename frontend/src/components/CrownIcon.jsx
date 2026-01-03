function CrownIcon({ size = 24, className = '' }) {
  // Генерируем уникальный ID для градиента, чтобы избежать конфликтов при множественном использовании
  const gradientId = `crownGradient-${Math.random().toString(36).substr(2, 9)}`
  
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Основание короны - прямоугольник с закругленными углами */}
      <rect
        x="4"
        y="18"
        width="16"
        height="2.5"
        rx="0.8"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Левая арка */}
      <path
        d="M5 18 Q5 12 6.5 8 Q7 6 7.5 6"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Полый кружок на левой арке */}
      <circle
        cx="7.5"
        cy="6"
        r="1"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
      />
      
      {/* Центральная арка - самая высокая */}
      <path
        d="M7.5 18 Q12 4 16.5 18"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Полый кружок на центральной арке */}
      <circle
        cx="12"
        cy="4"
        r="1"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
      />
      
      {/* Правая арка - зеркально левой */}
      <path
        d="M19 18 Q19 12 17.5 8 Q17 6 16.5 6"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Полый кружок на правой арке */}
      <circle
        cx="16.5"
        cy="6"
        r="1"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
      />
      
      <defs>
        {/* Золотой градиент для контура */}
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#ffc800" />
          <stop offset="50%" stopColor="#fff200" />
          <stop offset="100%" stopColor="#ffc800" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export default CrownIcon

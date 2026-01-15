function CrownIcon({ size = 24, className = '' }) {
  return (
    <img
      src="/main_korona.png"
      alt="Корона"
      width={size}
      height={size}
      className={className}
      style={{
        display: 'inline-block',
        objectFit: 'contain'
      }}
    />
  )
}

export default CrownIcon

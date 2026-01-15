// Применяем цвет из localStorage ДО импорта CSS, чтобы избежать мигания
(function() {
  try {
    const savedColor = localStorage.getItem('user-avatar-border-color');
    const availableColors = ['#ffffff', '#000000', '#808080', '#c4c4af', '#0066ff', '#00cc00', '#ff0000', '#ff69b4', '#ffd700', '#9932cc'];
    
    if (savedColor && availableColors.includes(savedColor)) {
      // Применяем базовые CSS переменные сразу
      const hex = savedColor.replace('#', '');
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      const rgba = `rgba(${r}, ${g}, ${b}, 0.1)`;
      const shadowRgba = `rgba(${r}, ${g}, ${b}, 0.2)`;
      
      document.documentElement.style.setProperty('--user-accent-color', savedColor);
      document.documentElement.style.setProperty('--user-accent-color-rgba', rgba);
      document.documentElement.style.setProperty('--user-accent-color-shadow', shadowRgba);
    }
  } catch (e) {
    // Игнорируем ошибки
  }
})();

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


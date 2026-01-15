import { useState, useEffect } from 'react'
import { documentsAPI } from '../services/api'
import './TermsOfUsePage.css'

function TermsOfUsePage() {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true)
        const data = await documentsAPI.getTermsOfUse()
        setContent(typeof data === 'string' ? data : data.message || data)
        setError('')
      } catch (err) {
        setError('Ошибка при загрузке документа')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchContent()
  }, [])

  if (loading) {
    return (
      <div className="document-page">
        <div className="document-container">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-page">
        <div className="document-container">
          <div className="error">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="document-page">
      <div className="document-container">
        <h1>Условия использования</h1>
        <div className="document-content">
          {content.split('\n').map((line, index) => (
            <p key={index}>{line || '\u00A0'}</p>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TermsOfUsePage

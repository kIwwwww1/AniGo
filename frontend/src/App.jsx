import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WatchPage from './pages/WatchPage'
import Layout from './components/Layout'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/watch/:animeId" element={<WatchPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App


import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WatchPage from './pages/WatchPage'
import WatchPageSearch from './pages/WatchPageSearch'
import MyFavoritesPage from './pages/MyFavoritesPage'
import UserProfilePage from './pages/UserProfilePage'
import PopularAnimePage from './pages/PopularAnimePage'
import Layout from './components/Layout'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/my" element={<MyFavoritesPage />} />
          <Route path="/watch/:animeId" element={<WatchPage />} />
          <Route path="/watch/search/:animeName" element={<WatchPageSearch />} />
          <Route path="/profile/:username" element={<UserProfilePage />} />
          <Route path="/anime/all/popular" element={<PopularAnimePage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App


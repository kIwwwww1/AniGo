import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WatchPage from './pages/WatchPage'
import WatchPageSearch from './pages/WatchPageSearch'
import MyFavoritesPage from './pages/MyFavoritesPage'
import UserProfilePage from './pages/UserProfilePage'
import PopularAnimePage from './pages/PopularAnimePage'
import AllAnimePage from './pages/AllAnimePage'
import Layout from './components/Layout'
import ScrollToTop from './components/ScrollToTop'

function App() {
  return (
    <Router>
      <ScrollToTop />
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/my" element={<MyFavoritesPage />} />
          <Route path="/watch/:animeId" element={<WatchPage />} />
          <Route path="/watch/search/:animeName" element={<WatchPageSearch />} />
          <Route path="/profile/:username" element={<UserProfilePage />} />
          <Route path="/anime/all/popular" element={<PopularAnimePage />} />
          <Route path="/anime/all/anime" element={<AllAnimePage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App


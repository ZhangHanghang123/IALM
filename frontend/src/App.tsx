import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import MatchAnalysis from './pages/MatchAnalysis'
import AlgorithmList from './pages/AlgorithmList'
import History from './pages/History'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<MainLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/companies" element={<Companies />} />
        <Route path="/match" element={<MatchAnalysis />} />
        <Route path="/algorithms" element={<AlgorithmList />} />
        <Route path="/history" element={<History />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
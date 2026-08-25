import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import RegulatoryOverview from './pages/RegulatoryOverview'
import Companies from './pages/Companies'
import Assets from './pages/Assets'
import Liabilities from './pages/Liabilities'
import MarketData from './pages/MarketData'
import MatchAnalysis from './pages/MatchAnalysis'
import DurationMatch from './pages/DurationMatch'
import CostYield from './pages/CostYield'
import CashflowPayback from './pages/CashflowPayback'
import CashflowForecast from './pages/CashflowForecast'
import Stress from './pages/Stress'
import Portfolio from './pages/Portfolio'
import Risk from './pages/Risk'
import AlgorithmList from './pages/AlgorithmList'
import Models from './pages/Models'
import History from './pages/History'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<MainLayout />}>
        {/* 首页概览 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/regulatory-overview" element={<RegulatoryOverview />} />

        {/* 基础数据 */}
        <Route path="/companies" element={<Companies />} />
        <Route path="/assets-list" element={<Assets />} />
        <Route path="/liabilities-list" element={<Liabilities />} />
        <Route path="/market-data" element={<MarketData />} />

        {/* 5号规则分析 */}
        <Route path="/match" element={<MatchAnalysis />} />
        <Route path="/duration-match" element={<DurationMatch />} />
        <Route path="/cost-yield" element={<CostYield />} />
        <Route path="/cashflow-payback" element={<CashflowPayback />} />

        {/* 现金流预测 */}
        <Route path="/cashflow-forecast" element={<CashflowForecast />} />
        <Route path="/monte-carlo" element={<CashflowForecast />} />

        {/* 压力测试 */}
        <Route path="/stress-scenarios" element={<Stress />} />
        <Route path="/stress-results" element={<Stress />} />
        <Route path="/stress-run" element={<Stress />} />

        {/* 投资组合 */}
        <Route path="/markowitz" element={<Portfolio />} />
        <Route path="/black-litterman" element={<Portfolio />} />
        <Route path="/allocations" element={<Portfolio />} />
        <Route path="/attributions" element={<Portfolio />} />

        {/* 风险与监管 */}
        <Route path="/risk-preferences" element={<Risk />} />
        <Route path="/risk-indicators" element={<Risk />} />
        <Route path="/risk-events" element={<Risk />} />
        <Route path="/regulatory-reports" element={<Risk />} />

        {/* 算法引擎 */}
        <Route path="/algorithms" element={<AlgorithmList />} />
        <Route path="/models" element={<Models />} />
        <Route path="/model-versions" element={<Models />} />
        <Route path="/history" element={<History />} />

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}
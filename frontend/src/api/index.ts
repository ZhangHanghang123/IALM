import axios from 'axios'

// 沿用 ALMD/IALMD 风格：baseURL='/ialm/api'
const api = axios.create({
  baseURL: '/ialm/api',
  timeout: 30000,
})

// 请求拦截：自动加 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ialm_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 跳登录
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ialm_token')
      if (!window.location.pathname.startsWith('/ialm/login')) {
        window.location.href = '/ialm/login'
      }
    }
    return Promise.reject(err)
  },
)

// ═══ 认证 ═══
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }).toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
}

// ═══ 保险公司 ═══
export const companiesApi = {
  list: (params?: any) => api.get('/companies', { params }),
  create: (data: any) => api.post('/companies', data),
  update: (id: number, data: any) => api.put(`/companies/${id}`, data),
  delete: (id: number) => api.delete(`/companies/${id}`),
}

// ═══ 5号规则算法 ═══
export const algorithmsApi = {
  list: () => api.get('/algorithms/rule5/algorithms'),
  fullAnalysis: (data: any) => api.post('/algorithms/rule5/full-analysis', data),
  history: (params?: any) => api.get('/algorithms/rule5/history', { params }),
  aggregateCashflows: (params: any) => api.get('/algorithms/rule5/aggregate-cashflows', { params }),
}

// ═══ 资产端 ═══
export const assetsApi = {
  categories: (params?: any) => api.get('/assets/categories', { params }),
  createCategory: (data: any) => api.post('/assets/categories', data),
  holdings: (params?: any) => api.get('/assets/holdings', { params }),
  createHolding: (data: any) => api.post('/assets/holdings', data),
  deleteHolding: (id: number) => api.delete(`/assets/holdings/${id}`),
  cashflows: (params?: any) => api.get('/assets/cashflows', { params }),
}

// ═══ 负债端 ═══
export const liabilitiesApi = {
  productCategories: (params?: any) => api.get('/liabilities/product-categories', { params }),
  createProductCategory: (data: any) => api.post('/liabilities/product-categories', data),
  policies: (params?: any) => api.get('/liabilities/policies', { params }),
  createPolicy: (data: any) => api.post('/liabilities/policies', data),
  cashflows: (params?: any) => api.get('/liabilities/cashflows', { params }),
  reserves: (params?: any) => api.get('/liabilities/reserves', { params }),
  assumptions: (params?: any) => api.get('/liabilities/assumptions', { params }),
}

// ═══ 市场数据 ═══
export const marketDataApi = {
  yieldCurves: (params?: any) => api.get('/market-data/yield-curves', { params }),
  yieldCurvePoints: (curveId: number) => api.get(`/market-data/yield-curves/${curveId}/points`),
  fxRates: (params?: any) => api.get('/market-data/fx-rates', { params }),
  equityIndices: (params?: any) => api.get('/market-data/equity-indices', { params }),
  creditSpreads: (params?: any) => api.get('/market-data/credit-spreads', { params }),
}

// ═══ 压力测试 ═══
export const stressApi = {
  scenarios: (params?: any) => api.get('/stress/scenarios', { params }),
  results: (params?: any) => api.get('/stress/results', { params }),
  run: (data: any) => api.post('/stress/run', data),
}

// ═══ 投资组合 ═══
export const portfolioApi = {
  markowitz: (data: any) => api.post('/portfolio/markowitz', data),
  blackLitterman: (data: any) => api.post('/portfolio/black-litterman', data),
  allocations: (params?: any) => api.get('/portfolio/allocations', { params }),
  attributions: (params?: any) => api.get('/portfolio/attributions', { params }),
}

// ═══ 风险预警 ═══
export const riskApi = {
  preferences: (params?: any) => api.get('/risk/preferences', { params }),
  indicators: (params?: any) => api.get('/risk/indicators', { params }),
  events: (params?: any) => api.get('/risk/events', { params }),
  regulatoryReports: (params?: any) => api.get('/risk/regulatory-reports', { params }),
}

// ═══ 模型管理 ═══
export const modelsApi = {
  definitions: (params?: any) => api.get('/models/definitions', { params }),
  versions: (params?: any) => api.get('/models/versions', { params }),
  parameters: (params?: any) => api.get('/models/parameters', { params }),
}

// ═══ 系统/字典 ═══
export const systemApi = {
  health: () => api.get('/health'),
  periodUnits: () => api.get('/system/period-units'),
}

export default api
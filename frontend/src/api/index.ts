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
}

// ═══ 系统 ═══
export const systemApi = {
  health: () => api.get('/health'),
}

export default api
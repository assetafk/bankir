import axios from 'axios'

const s = process.env.REACT_APP_API_URL || '/api/v1'

const api = axios.create({
  baseURL: s,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => {
    const formData = new URLSearchParams()
    formData.append('username', data.email)
    formData.append('password', data.password)
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  getMe: () => api.get('/auth/me'),
}

export const accountsAPI = {
  create: (data) => api.post('/accounts', data),
  getAll: () => api.get('/accounts'),
  getById: (id) => api.get(`/accounts/${id}`),
}

export const transfersAPI = {
  transfer: (data, idempotencyKey) =>
    api.post('/transfers', data, {
      headers: { 'Idempotency-Key': idempotencyKey },
    }),
}

export const transactionsAPI = {
  getHistory: (params) => api.get('/transactions', { params }),
}

export default api

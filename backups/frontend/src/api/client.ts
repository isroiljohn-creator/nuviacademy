import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
    baseURL: API_BASE
})

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

export const authAPI = {
    telegramAuth: (initData: string) => api.post('/auth/telegram', { initData })
}

export const userAPI = {
    getProfile: () => api.get('/user/profile'),
    updateProfile: (data: any) => api.put('/user/profile', data)
}

export const aiAPI = {
    generateWorkout: () => api.post('/ai/workout'),
    generateMeal: () => api.post('/ai/meal')
}

export const premiumAPI = {
    getStatus: () => api.get('/premium/status')
}

export const referralAPI = {
    getInfo: () => api.get('/referral/info')
}

export const analyticsAPI = {
    getDailyLogs: (days: number = 7) => api.get(`/analytics/daily?days=${days}`)
}

export const adminAPI = {
    getStats: () => api.get('/admin/stats')
}

export default api

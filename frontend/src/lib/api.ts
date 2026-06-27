import axios from 'axios'
import Cookies from 'js-cookie'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = Cookies.get('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      Cookies.remove('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Auth
export const register = (data: { email: string; name: string; password: string }) =>
  api.post('/auth/register', data)

export const login = (data: { email: string; password: string }) =>
  api.post('/auth/login', data)

// Projects
export const createProject = (data: object) => api.post('/projects/', data)
export const getProjects = () => api.get('/projects/')
export const getProject = (id: number) => api.get(`/projects/${id}`)
export const deleteProject = (id: number) => api.delete(`/projects/${id}`)

// Reports
export const getReport = (projectId: number) => api.get(`/reports/${projectId}`)
export const getPdfReport = (projectId: number) =>
  `${API_URL}/reports/${projectId}/pdf`
export const getJsonReport = (projectId: number) =>
  `${API_URL}/reports/${projectId}/json`

// Profile / Audience / Competitors
export const getProfile = () => api.get('/profile/')
export const saveProfile = (data: object) => api.post('/profile/', data)
export const getAudience = () => api.get('/profile/audience')
export const getCompetitors = () => api.get('/profile/competitors')
export const regenerateCompetitors = () => api.post('/profile/regenerate-competitors')

// Prompt Agent
export const generatePromptAgent = (projectId?: number) =>
  api.post('/prompt-agent/generate', null, { params: projectId ? { project_id: projectId } : {} })
export const getLatestPromptAgent = () => api.get('/prompt-agent/latest')

// Social Media Strategy Agent
export const generateSocialCalendar = (data: { platforms: string[]; month?: string }) =>
  api.post('/social/generate-calendar', data)
export const listCalendars = () => api.get('/social/calendars')
export const getCalendarDetail = (id: number) => api.get(`/social/calendars/${id}`)
export const updatePostStatus = (postId: number, data: object) => api.patch(`/social/posts/${postId}`, data)

// Analytics
export const getSeoAnalytics = () => api.get('/analytics/seo')
export const getCompetitorAnalytics = () => api.get('/analytics/competitors')
export const getAudienceAnalytics = () => api.get('/analytics/audience')
export const getSocialAnalytics = () => api.get('/analytics/social')
export const getAgentAnalytics = () => api.get('/analytics/agents')

// Notifications
export const getNotifications = () => api.get('/notifications/')
export const getUnreadCount = () => api.get('/notifications/unread-count')
export const markNotificationRead = (id: number) => api.patch(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => api.patch('/notifications/read-all')

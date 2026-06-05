import axios from "axios"
import { useAuthStore } from "../store/authStore"

export const api = axios.create({
  baseURL: "http://localhost:8000/api/v1", // Adjust as per your backend
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor: add token to headers
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle 401s
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

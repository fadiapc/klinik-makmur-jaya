import { useEffect, useState, useCallback } from "react"
import { useAuthStore } from "../store/authStore"
import { api } from "../lib/api"

export interface WebSocketAlert {
  id?: string | number
  timestamp?: number
  type: string
  notif_type?: string
  level: "info" | "success" | "warning" | "error"
  title: string
  message: string
  link?: string
  is_read?: boolean
}

export function useWebSocket() {
  const { token, isAuthenticated } = useAuthStore()
  const [lastAlert, setLastAlert] = useState<WebSocketAlert | null>(null)
  const [notifications, setNotifications] = useState<WebSocketAlert[]>([])
  const [isConnected, setIsConnected] = useState(false)

  const fetchInitialNotifications = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      const res = await api.get("/notifications")
      if (res.data && res.data.items) {
        setNotifications(res.data.items.map((n: any) => ({
          id: n.id,
          timestamp: new Date(n.created_at).getTime(),
          type: "alert",
          notif_type: n.type,
          level: n.level,
          title: n.title,
          message: n.message,
          link: n.link,
          is_read: n.is_read
        })))
      }
    } catch (err) {
      console.error("Failed to fetch initial notifications", err)
    }
  }, [isAuthenticated])

  useEffect(() => {
    fetchInitialNotifications()
  }, [fetchInitialNotifications])

  const connect = useCallback(() => {
    if (!isAuthenticated || !token) return

    // Ensure we use the correct WebSocket protocol
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    // Assume backend runs on same host, port 8000 (adjust if using vite proxy)
    const wsHost = import.meta.env.VITE_API_URL 
      ? import.meta.env.VITE_API_URL.replace("http", "ws")
      : `${protocol}//localhost:8000/api/v1`
      
    // Replace /api/v1 with /ws to point to WebSocket router
    const wsUrl = wsHost.replace("/api/v1", "") + `/ws/alerts?token=${token}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data: WebSocketAlert = JSON.parse(event.data)
        if (data.type === "alert") {
          const newAlert = { 
            ...data, 
            id: data.id || Math.random().toString(36).substring(7), 
            timestamp: data.timestamp || Date.now(), 
            is_read: false 
          }
          setLastAlert(newAlert)
          setNotifications(prev => [newAlert, ...prev].slice(0, 50))
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message", err)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      // Attempt to reconnect after 5 seconds
      setTimeout(connect, 5000)
    }

    return () => {
      ws.close()
    }
  }, [token, isAuthenticated])

  useEffect(() => {
    const cleanup = connect()
    return () => {
      if (cleanup) cleanup()
    }
  }, [connect])

  const clearAlert = () => setLastAlert(null)
  
  const markAsRead = async (id: string | number) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
    try {
      await api.post(`/notifications/${id}/read`)
    } catch (err) {
      console.error("Failed to mark as read", err)
    }
  }
  
  const markAllAsRead = async () => {
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    try {
      await api.post(`/notifications/read-all`)
    } catch (err) {
      console.error("Failed to mark all as read", err)
    }
  }

  return { isConnected, lastAlert, clearAlert, notifications, markAsRead, markAllAsRead }
}

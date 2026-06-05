import { useEffect, useState, useCallback } from "react"
import { useAuthStore } from "../store/authStore"

interface WebSocketAlert {
  id?: string
  timestamp?: number
  type: string
  level: "info" | "success" | "warning" | "error"
  title: string
  message: string
  link?: string
  read?: boolean
}

export function useWebSocket() {
  const { token, isAuthenticated } = useAuthStore()
  const [lastAlert, setLastAlert] = useState<WebSocketAlert | null>(null)
  const [notifications, setNotifications] = useState<WebSocketAlert[]>([])
  const [isConnected, setIsConnected] = useState(false)

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
          const newAlert = { ...data, id: Math.random().toString(36).substring(7), timestamp: Date.now(), read: false }
          setLastAlert(newAlert)
          setNotifications(prev => [newAlert, ...prev].slice(0, 20))
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
  
  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
  }
  
  const clearAllNotifications = () => {
    setNotifications([])
  }

  return { isConnected, lastAlert, clearAlert, notifications, markAsRead, clearAllNotifications }
}

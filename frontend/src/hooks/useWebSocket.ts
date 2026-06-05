import { useEffect, useState, useCallback } from "react"
import { useAuthStore } from "../store/authStore"

interface WebSocketAlert {
  type: string
  level: "info" | "success" | "warning" | "error"
  title: string
  message: string
  link?: string
}

export function useWebSocket() {
  const { token, isAuthenticated } = useAuthStore()
  const [lastAlert, setLastAlert] = useState<WebSocketAlert | null>(null)
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
          setLastAlert(data)
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

  return { isConnected, lastAlert, clearAlert }
}

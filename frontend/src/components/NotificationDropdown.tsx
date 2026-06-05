import { useState, useRef, useEffect } from "react"
import { Bell, X, CheckCircle2, AlertCircle, Info, Package, AlertTriangle, Clock } from "lucide-react"
import { useWebSocket } from "../hooks/useWebSocket"
import { useNavigate } from "react-router-dom"

export default function NotificationDropdown() {
  const { notifications, markAsRead, markAllAsRead } = useWebSocket()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  const unreadCount = notifications.filter(n => !n.is_read).length

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

  const handleNotificationClick = (notif: any) => {
    if (!notif.is_read) {
      markAsRead(notif.id)
    }
    if (notif.link) {
      navigate(notif.link)
      setIsOpen(false)
    }
  }

  const getIcon = (level: string, type: string) => {
    if (type === "order") return <Package className="w-5 h-5 text-indigo-500" />
    if (type === "stock") return <AlertTriangle className="w-5 h-5 text-orange-500" />
    if (type === "expiry") return <Clock className="w-5 h-5 text-red-500" />
    
    switch (level) {
      case "success": return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case "warning": return <AlertCircle className="w-5 h-5 text-orange-500" />
      case "error": return <AlertCircle className="w-5 h-5 text-red-500" />
      default: return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getTimeAgo = (timestamp: number) => {
    const diff = Math.floor((Date.now() - timestamp) / 1000)
    if (diff < 60) return `${diff} detik lalu`
    if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`
    if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
    return `${Math.floor(diff / 86400)} hari lalu`
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen((o) => !o)}
        className="relative w-9 h-9 flex items-center justify-center rounded-full hover:bg-slate-100 transition-colors text-slate-600 focus:outline-none"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white animate-pulse" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-11 w-80 sm:w-96 bg-white rounded-xl border border-slate-200 shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200 flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b bg-slate-50 shrink-0">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-800 text-sm">Notifikasi</h3>
              {unreadCount > 0 && (
                <span className="bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {unreadCount} baru
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Tandai baca
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-700 w-6 h-6 flex items-center justify-center rounded-md hover:bg-slate-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="max-h-[60vh] overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                <Bell className="w-10 h-10 mb-3 text-slate-300" />
                <p className="text-sm font-medium">Tidak ada notifikasi</p>
                <p className="text-xs mt-1 text-slate-400 text-center max-w-[200px]">
                  Pemberitahuan terkait pesanan dan stok akan muncul di sini.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => handleNotificationClick(notif)}
                    className={`p-4 flex gap-3 transition-colors cursor-pointer ${
                      notif.is_read ? "bg-white hover:bg-slate-50" : "bg-blue-50/30 hover:bg-blue-50/50"
                    }`}
                  >
                    <div className="shrink-0 mt-0.5">
                      {getIcon(notif.level, notif.notif_type || notif.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p className={`text-sm font-semibold truncate ${notif.is_read ? 'text-slate-700' : 'text-slate-900'}`}>
                          {notif.title}
                        </p>
                        <span className="text-[10px] text-slate-400 whitespace-nowrap shrink-0">
                          {notif.timestamp ? getTimeAgo(notif.timestamp) : 'Baru saja'}
                        </span>
                      </div>
                      <p className={`text-xs leading-snug line-clamp-2 ${notif.is_read ? 'text-slate-500' : 'text-slate-600'}`}>
                        {notif.message}
                      </p>
                    </div>
                    {!notif.is_read && (
                      <div className="shrink-0 flex items-center">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

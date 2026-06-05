import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useWebSocket } from "../../hooks/useWebSocket"
import { useState, useRef, useEffect } from "react"
import { LogOut, LayoutDashboard, Package, ExternalLink, Users, ShieldCheck, X, FileText, Bell, Check, Trash2 } from "lucide-react"

export default function ProtectedLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()
  const { lastAlert, clearAlert, notifications, markAsRead, clearAllNotifications } = useWebSocket()

  const [showNotifications, setShowNotifications] = useState(false)
  const notificationRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const isAdmin = user?.role?.name?.toLowerCase() === 'admin'
  const unreadCount = notifications.filter(n => !n.read).length

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col shadow-sm">
        <div className="py-4 flex flex-col justify-center px-6 border-b h-20">
          <Link to="/dashboard" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-10 h-10 object-contain" />
            <div className="font-bold leading-tight">
              <span className="block text-slate-900 text-sm">Klinik</span>
              <span className="block text-primary text-xl">Makmur Jaya</span>
            </div>
          </Link>
        </div>
        
        <div className="p-4 border-b bg-slate-50/50">
          <p className="text-sm font-medium text-slate-900">{user?.name}</p>
          <p className="text-xs text-slate-500 capitalize">{user?.role?.name} Role</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <Link to="/dashboard" className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${location.pathname === '/dashboard' ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100'}`}>
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </Link>
          <Link to="/admin/products" className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${location.pathname.startsWith('/admin/products') ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100'}`}>
            <Package className="w-4 h-4" />
            Kelola Produk
          </Link>
          
          {isAdmin && (
            <>
              <Link
                to="/admin/users"
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname.startsWith("/admin/users") 
                    ? "bg-primary/10 text-primary" 
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Users className="w-4 h-4" />
                Kelola Pengguna
              </Link>
              
              <Link
                to="/admin/audit"
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname.startsWith("/admin/audit") 
                    ? "bg-primary/10 text-primary" 
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                Audit Keamanan
              </Link>
            </>
          )}
          
          <div className="pt-4 mt-4 border-t border-slate-200">
            <a href="/catalog" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-3 py-2 rounded-md text-slate-500 hover:text-primary hover:bg-slate-100 text-sm font-medium transition-colors">
              <ExternalLink className="w-4 h-4" />
              Lihat Toko
            </a>
          </div>
        </nav>

        <div className="p-4 border-t">
          <button 
            onClick={() => logout()}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-red-600 hover:bg-red-50 text-sm font-medium transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50">
        {/* Header */}
        <header className="h-16 bg-white border-b flex items-center justify-end px-6 shadow-sm shrink-0 z-20 relative">
          <div className="relative" ref={notificationRef}>
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white border rounded-xl shadow-lg z-50 overflow-hidden flex flex-col max-h-[32rem]">
                <div className="p-3 border-b bg-slate-50 flex justify-between items-center shrink-0">
                  <h3 className="font-semibold text-slate-800 text-sm">Notifikasi</h3>
                  {notifications.length > 0 && (
                    <button 
                      onClick={clearAllNotifications}
                      className="text-xs text-slate-500 hover:text-red-600 flex items-center gap-1 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" /> Bersihkan
                    </button>
                  )}
                </div>
                
                <div className="overflow-y-auto flex-1">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-sm text-slate-500">
                      Tidak ada notifikasi
                    </div>
                  ) : (
                    <div className="divide-y">
                      {notifications.map((notif) => (
                        <div 
                          key={notif.id} 
                          className={`p-3 hover:bg-slate-50 transition-colors flex gap-3 cursor-pointer ${!notif.read ? 'bg-blue-50/50' : ''}`}
                          onClick={() => { if(!notif.read && notif.id) markAsRead(notif.id) }}
                        >
                          <div className={`p-2 rounded-full h-fit shrink-0 ${
                            notif.level === 'success' ? 'bg-primary/10 text-primary' : 
                            notif.level === 'error' ? 'bg-red-100 text-red-600' : 
                            notif.level === 'warning' ? 'bg-amber-100 text-amber-600' :
                            'bg-blue-100 text-blue-600'
                          }`}>
                            {notif.link ? <FileText className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className={`text-sm ${!notif.read ? 'font-semibold text-slate-800' : 'font-medium text-slate-700'}`}>
                              {notif.title}
                            </h4>
                            <p className="text-xs text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">
                              {notif.message}
                            </p>
                            <div className="flex justify-between items-center mt-2">
                              <span className="text-[10px] text-slate-400 font-medium">
                                {notif.timestamp ? new Date(notif.timestamp).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : ''}
                              </span>
                              {!notif.read && (
                                <button 
                                  onClick={(e) => { e.stopPropagation(); if(notif.id) markAsRead(notif.id) }}
                                  className="text-[10px] text-primary hover:text-primary/80 font-medium flex items-center gap-1"
                                >
                                  <Check className="w-3 h-3" /> Tandai dibaca
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* WebSocket Global Toast */}
      {lastAlert && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5">
          <div className="bg-white border border-slate-200 shadow-lg rounded-xl p-4 w-80 relative flex gap-3">
            <button 
              onClick={clearAlert}
              className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
            <div className={`p-2 rounded-full h-fit ${
              lastAlert.level === 'success' ? 'bg-primary/10 text-primary' : 
              lastAlert.level === 'error' ? 'bg-red-100 text-red-600' : 
              'bg-blue-100 text-blue-600'
            }`}>
              {lastAlert.link ? <FileText className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-slate-800 text-sm mb-1">{lastAlert.title}</h4>
              <p className="text-slate-600 text-sm">{lastAlert.message}</p>
              {lastAlert.link && (
                <a 
                  href={`${import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'}${lastAlert.link}`}
                  target="_blank" rel="noopener noreferrer"
                  className="mt-3 inline-block bg-primary text-white text-xs px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition"
                  onClick={clearAlert}
                >
                  Download Laporan
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useWebSocket } from "../../hooks/useWebSocket"
import { LogOut, LayoutDashboard, Package, ExternalLink, Users, ShieldCheck, X, FileText, Settings } from "lucide-react"

export default function ProtectedLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()
  const { lastAlert, clearAlert } = useWebSocket()

  const isAdmin = user?.role?.name?.toLowerCase() === 'admin'

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

              <Link
                to="/admin/settings"
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname.startsWith("/admin/settings") 
                    ? "bg-primary/10 text-primary" 
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Settings className="w-4 h-4" />
                Pengaturan Sistem
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
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

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

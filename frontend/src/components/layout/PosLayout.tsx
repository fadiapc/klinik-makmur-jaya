import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { LogOut, Bell } from "lucide-react"
import NotificationDropdown from "../NotificationDropdown"

export default function PosLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Hanya kasir (atau admin) yang boleh masuk POS
  const roleName = user?.role?.name?.toLowerCase() || ''
  if (roleName !== 'kasir' && roleName !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="h-16 bg-white border-b flex items-center justify-between px-6 shadow-sm z-10 shrink-0">
        <div className="flex items-center gap-6 lg:gap-12">
          {/* Logo Section */}
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-9 h-9 object-contain" />
            <div className="flex flex-col leading-none font-bold">
              <span className="text-slate-800 text-[13px] tracking-wide">Klinik</span>
              <span className="text-primary text-[19px] tracking-tight">Makmur Jaya</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Navigation Menus */}
          <div className="flex items-center gap-2 mr-4">
            <Link 
              to="/pos" 
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${location.pathname === '/pos' ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              POS Kasir
            </Link>
            <Link 
              to="/pos/orders" 
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${location.pathname === '/pos/orders' ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              Pesanan Online
            </Link>
            <div className="flex items-center ml-2">
              <NotificationDropdown />
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">{user?.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user?.role?.name}</p>
          </div>
          
          <div className="h-8 w-px bg-slate-200"></div>

          <button 
            onClick={() => logout()}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-red-600 hover:bg-red-50 text-sm font-medium transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden flex flex-col relative">
        <Outlet />
      </main>
    </div>
  )
}

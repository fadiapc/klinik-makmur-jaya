import { Navigate, Outlet } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { LogOut } from "lucide-react"

export default function PosLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()

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

          {/* Title Section */}
          <div className="hidden md:flex items-center gap-4 font-bold border-l pl-6 border-slate-200">
            <span className="text-primary text-sm tracking-wide">Sistem POS Kasir</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-800 text-lg">Katalog Obat</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
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

import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { LogOut, LayoutDashboard, Package, ExternalLink, Users } from "lucide-react"

export default function ProtectedLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col shadow-sm">
        <div className="py-4 flex flex-col justify-center px-6 border-b h-20">
          <Link to="/dashboard" className="font-bold leading-tight">
            <span className="block text-slate-900 text-sm">Klinik</span>
            <span className="block text-primary text-xl">Makmur Jaya</span>
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
          
          {user?.role?.name?.toLowerCase() === 'admin' && (
            <Link to="/admin/users" className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${location.pathname.startsWith('/admin/users') ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100'}`}>
              <Users className="w-4 h-4" />
              Kelola Pengguna
            </Link>
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

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  )
}

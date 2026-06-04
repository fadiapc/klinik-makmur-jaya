import { Navigate, Outlet, Link } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { LogOut, LayoutDashboard, Package, ShoppingCart } from "lucide-react"

export default function ProtectedLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col shadow-sm">
        <div className="h-16 flex items-center px-6 border-b">
          <Link to="/catalog" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            Makmur Jaya
          </Link>
        </div>
        
        <div className="p-4 border-b bg-slate-50/50">
          <p className="text-sm font-medium text-slate-900">{user?.full_name}</p>
          <p className="text-xs text-slate-500 capitalize">{user?.role} Role</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <Link to="/dashboard" className="flex items-center gap-3 px-3 py-2 rounded-md bg-blue-50 text-blue-700 text-sm font-medium">
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </Link>
          <Link to="/catalog" className="flex items-center gap-3 px-3 py-2 rounded-md text-slate-600 hover:bg-slate-100 text-sm font-medium transition-colors">
            <Package className="w-4 h-4" />
            Katalog Obat
          </Link>
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

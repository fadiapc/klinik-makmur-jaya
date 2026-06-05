import { Navigate, Outlet, Link, useLocation } from "react"
import { useAuthStore } from "../../store/authStore"
import { useCartStore } from "../../store/cartStore"
import { useWebSocket } from "../../hooks/useWebSocket"
import { LogOut, ShoppingCart, User, ClipboardList, Package, Bell, FileText, X } from "lucide-react"

export default function CustomerLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const { totalItems } = useCartStore()
  const location = useLocation()
  const { lastAlert, clearAlert } = useWebSocket()

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  // Double check if role is pasien, if not, redirect to dashboard
  if (user.role.name !== "pasien") {
    return <Navigate to="/dashboard" replace />
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/catalog" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
            <div className="text-xl font-bold leading-tight hidden md:block">
              <span className="text-slate-900">Klinik </span>
              <span className="text-blue-600">Makmur Jaya</span>
            </div>
          </Link>
          
          <nav className="flex items-center gap-2 md:gap-4">
            <Link 
              to="/catalog" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname.startsWith("/catalog") ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Package className="w-4 h-4" />
              <span className="hidden md:block">Katalog</span>
            </Link>
            
            <Link 
              to="/orders" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname.startsWith("/orders") ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <ClipboardList className="w-4 h-4" />
              <span className="hidden md:block">Pesanan Saya</span>
            </Link>

            <Link 
              to="/cart" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative ${
                location.pathname === "/cart" ? "text-blue-600 bg-blue-50" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <ShoppingCart className="w-4 h-4" />
              <span className="hidden md:block">Keranjang</span>
              {totalItems() > 0 && (
                <span className="absolute top-1 right-1 md:-top-1 md:-right-1 bg-red-500 text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
                  {totalItems()}
                </span>
              )}
            </Link>

            <div className="h-6 w-px bg-slate-200 mx-2 hidden md:block"></div>

            <div className="flex items-center gap-3 pl-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                <User className="w-4 h-4" />
              </div>
              <span className="text-sm font-semibold text-slate-900 hidden md:block">{user.name}</span>
              <button 
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </nav>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
      
      <footer className="border-t py-6 bg-white mt-auto">
        <div className="container mx-auto px-4 flex flex-col items-center justify-center gap-4">
          <p className="text-center text-sm text-slate-500">
            © 2025 Klinik Makmur Jaya. All rights reserved.
          </p>
        </div>
      </footer>

      {/* WebSocket Live Toast (auto-dismiss) */}
      {lastAlert && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5">
          <div className="bg-white border border-slate-200 shadow-xl rounded-xl p-4 w-80 relative flex gap-3">
            <button
              onClick={clearAlert}
              className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
            <div className={`p-2 rounded-full h-fit shrink-0 ${
              lastAlert.level === "success" ? "bg-green-100 text-green-600" :
              lastAlert.level === "error" ? "bg-red-100 text-red-600" :
              "bg-blue-100 text-blue-600"
            }`}>
              {lastAlert.link ? <FileText className="w-5 h-5" /> : <Bell className="w-5 h-5" />}
            </div>
            <div className="flex-1 pr-4">
              <h4 className="font-semibold text-slate-800 text-sm mb-1">{lastAlert.title}</h4>
              <p className="text-slate-600 text-sm">{lastAlert.message}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

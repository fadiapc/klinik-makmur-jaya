import { Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useCartStore } from "../../store/cartStore"
import { LogOut, ShoppingCart, User, Package, ClipboardList, LayoutDashboard } from "lucide-react"

export default function PublicLayout() {
  const { isAuthenticated, logout, user } = useAuthStore()
  const { totalItems } = useCartStore()
  const location = useLocation()

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
        <div className="w-full max-w-[1400px] mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/catalog" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
            <div className="text-xl font-bold leading-tight hidden md:block">
              <span className="text-slate-900">Klinik </span>
              <span className="text-primary">Makmur Jaya</span>
            </div>
          </Link>
          
          <nav className="flex items-center gap-2 md:gap-4">
            <Link 
              to="/catalog" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname.startsWith("/catalog") ? "text-teal-600 bg-teal-50" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Package className="w-4 h-4" />
              <span className="hidden md:block">Katalog</span>
            </Link>

            {isAuthenticated && user?.role?.name === "pasien" && (
              <Link 
                to="/orders" 
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname.startsWith("/orders") ? "text-teal-600 bg-teal-50" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <ClipboardList className="w-4 h-4" />
                <span className="hidden md:block">Riwayat Pesanan</span>
              </Link>
            )}

            {isAuthenticated && user?.role?.name !== "pasien" && (
              <Link 
                to="/dashboard" 
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname.startsWith("/dashboard") ? "text-teal-600 bg-teal-50" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span className="hidden md:block">Dashboard</span>
              </Link>
            )}
            
            <Link 
              to="/cart" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative ${
                location.pathname === "/cart" ? "text-teal-600 bg-teal-50" : "text-slate-600 hover:bg-slate-100"
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
            
            {isAuthenticated ? (
              <div className="flex items-center gap-3 pl-2">
                <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                  <User className="w-4 h-4" />
                </div>
                <span className="text-sm font-semibold text-slate-900 hidden md:block">{user?.name}</span>
                <button 
                  onClick={() => logout()}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="ml-2 flex items-center gap-2">
                <Link 
                  to="/login" 
                  className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background border border-slate-200 bg-white hover:bg-slate-100 hover:text-slate-900 h-9 py-2 px-4 shadow-sm"
                >
                  Masuk
                </Link>
                <Link 
                  to="/register" 
                  className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-teal-500 text-white hover:bg-teal-600 h-9 py-2 px-4 shadow-sm"
                >
                  Daftar
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
      
      <footer className="border-t py-6 md:py-0 bg-white">
        <div className="container mx-auto px-4 flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
          <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
            © 2025 Klinik Makmur Jaya. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

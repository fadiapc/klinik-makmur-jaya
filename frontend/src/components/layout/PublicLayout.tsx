import { Outlet, Link } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useCartStore } from "../../store/cartStore"
import { LogOut, ShoppingCart } from "lucide-react"

export default function PublicLayout() {
  const { isAuthenticated, logout, user } = useAuthStore()
  const { totalItems } = useCartStore()

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
        <div className="w-full max-w-[1400px] mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/catalog" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-10 h-10 md:w-12 md:h-12 object-contain" />
            <div className="text-2xl md:text-3xl font-bold leading-tight">
              <span className="text-slate-900">Klinik </span>
              <span className="text-primary">Makmur Jaya</span>
            </div>
          </Link>
          
          <nav className="flex items-center gap-4">
            <div className="flex items-center gap-6">
              <Link to="/catalog" className="text-sm font-medium text-slate-600 hover:text-teal-600 transition-colors">
                Katalog
              </Link>
              
              <Link to="/cart" className="relative text-slate-600 hover:text-teal-600 transition-colors p-1 flex items-center">
                <ShoppingCart className="w-5 h-5" />
                {totalItems() > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
                    {totalItems()}
                  </span>
                )}
              </Link>
            </div>
            
            <div className="h-6 w-px bg-slate-200 mx-2"></div>
            
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                {user?.role.name === "pasien" && (
                  <Link to="/orders" className="text-sm font-medium text-slate-600 hover:text-teal-600 transition-colors">
                    Pesanan Saya
                  </Link>
                )}
                {user?.role.name !== "pasien" && (
                  <Link to="/dashboard" className="text-sm font-medium text-slate-600 hover:text-teal-600 transition-colors">
                    Dashboard
                  </Link>
                )}
                <div className="h-4 w-px bg-slate-200"></div>
                <span className="text-sm font-medium text-slate-900">{user?.name}</span>
                <button 
                  onClick={() => logout()}
                  className="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="ml-4 flex items-center gap-2">
                <Link 
                  to="/login" 
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background border border-slate-200 bg-white hover:bg-slate-100 hover:text-slate-900 h-10 py-2 px-4 shadow-sm"
                >
                  Masuk
                </Link>
                <Link 
                  to="/register" 
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-teal-500 text-white hover:bg-teal-600 h-10 py-2 px-4 shadow-sm"
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

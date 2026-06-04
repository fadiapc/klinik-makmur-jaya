import { Outlet, Link } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { LogOut } from "lucide-react"

export default function PublicLayout() {
  const { isAuthenticated, logout, user } = useAuthStore()

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/catalog" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            Makmur Jaya
          </Link>
          
          <nav className="flex items-center gap-4">
            <Link to="/catalog" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
              Katalog
            </Link>
            
            {isAuthenticated ? (
              <div className="flex items-center gap-4 ml-4">
                <Link to="/dashboard" className="text-sm font-medium text-slate-600 hover:text-blue-600">
                  Dashboard
                </Link>
                <div className="h-4 w-px bg-slate-200"></div>
                <span className="text-sm font-medium text-slate-900">{user?.full_name}</span>
                <button 
                  onClick={() => logout()}
                  className="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            ) : (
              <Link 
                to="/login" 
                className="ml-4 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-blue-600 text-white hover:bg-blue-700 h-10 py-2 px-4 shadow-sm"
              >
                Login
              </Link>
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

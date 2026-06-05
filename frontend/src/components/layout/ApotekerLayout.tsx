import { useState } from "react"
import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useWebSocket } from "../../hooks/useWebSocket"
import {
  LogOut, LayoutDashboard, ClipboardList, Package, X,
  ShieldCheck, FileText, Bell
} from "lucide-react"

export default function ApotekerLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()
  const { lastAlert, clearAlert } = useWebSocket()
  const [notifOpen, setNotifOpen] = useState(false)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const roleName = user?.role?.name?.toLowerCase() || ""
  if (roleName !== "apoteker" && roleName !== "admin") {
    return <Navigate to="/admin/dashboard" replace />
  }

  const navItems = [
    { to: "/apoteker", label: "Dashboard", icon: LayoutDashboard, exact: true },
    { to: "/apoteker/verifikasi", label: "Riwayat Resep", icon: ClipboardList },
    { to: "/apoteker/orders", label: "Pengiriman Pesanan", icon: Package },
    { to: "/apoteker/produk", label: "Kelola Produk", icon: Package },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col shadow-sm shrink-0">
        {/* Logo */}
        <div className="py-4 flex flex-col justify-center px-6 border-b h-20">
          <Link to="/apoteker" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-10 h-10 object-contain" />
            <div className="font-bold leading-tight">
              <span className="block text-slate-900 text-sm">Klinik</span>
              <span className="block text-primary text-xl">Makmur Jaya</span>
            </div>
          </Link>
        </div>

        {/* User Info */}
        <div className="p-4 border-b bg-slate-50/50">
          <p className="text-sm font-bold text-slate-900">{user?.name}</p>
          <p className="text-xs text-slate-500 capitalize">Role: {user?.role?.name}</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, exact }) => {
            const isActive = exact
              ? location.pathname === to
              : location.pathname.startsWith(to)
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive ? "bg-primary/10 text-primary" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            )
          })}
        </nav>

        {/* Logout */}
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

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Top Bar with Notification Bell */}
        <header className="h-14 bg-white border-b flex items-center justify-end px-6 shrink-0 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-700">{user?.name}</span>
            <span className="text-xs text-slate-400 capitalize bg-slate-100 px-2 py-0.5 rounded-full">
              {user?.role?.name}
            </span>

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setNotifOpen((o) => !o)}
                className="relative w-9 h-9 flex items-center justify-center rounded-full hover:bg-slate-100 transition-colors text-slate-600"
              >
                <Bell className="w-5 h-5" />
                {lastAlert && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
                )}
              </button>

              {/* Popup */}
              {notifOpen && (
                <>
                  {/* Backdrop */}
                  <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />

                  <div className="absolute right-0 top-11 w-80 bg-white rounded-xl border border-slate-200 shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="flex items-center justify-between px-4 py-3 border-b">
                      <h3 className="font-bold text-slate-800 text-sm">Notifikasi</h3>
                      <button
                        onClick={() => setNotifOpen(false)}
                        className="text-slate-400 hover:text-slate-700 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="max-h-72 overflow-y-auto">
                      {!lastAlert ? (
                        <div className="flex flex-col items-center justify-center py-10 text-slate-400">
                          <Bell className="w-8 h-8 mb-2 text-slate-300" />
                          <p className="text-sm">Tidak ada notifikasi baru</p>
                        </div>
                      ) : (
                        <div className="p-3">
                          <div className={`flex gap-3 p-3 rounded-xl border ${
                            lastAlert.level === "success"
                              ? "bg-green-50 border-green-100"
                              : lastAlert.level === "error"
                              ? "bg-red-50 border-red-100"
                              : "bg-blue-50 border-blue-100"
                          }`}>
                            <div className={`p-1.5 rounded-full h-fit ${
                              lastAlert.level === "success" ? "bg-green-100 text-green-600" :
                              lastAlert.level === "error" ? "bg-red-100 text-red-600" :
                              "bg-blue-100 text-blue-600"
                            }`}>
                              {lastAlert.link ? <FileText className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-slate-800 text-sm">{lastAlert.title}</p>
                              <p className="text-slate-600 text-xs mt-0.5">{lastAlert.message}</p>
                              {lastAlert.link && (
                                <a
                                  href={`${import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000"}${lastAlert.link}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="mt-2 inline-block text-xs bg-primary text-white px-3 py-1 rounded-lg font-medium hover:bg-primary/90"
                                >
                                  Download
                                </a>
                              )}
                            </div>
                            <button
                              onClick={() => { clearAlert(); setNotifOpen(false) }}
                              className="text-slate-400 hover:text-slate-700 shrink-0"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* WebSocket Live Toast (auto-dismiss) */}
      {lastAlert && !notifOpen && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5">
          <div className="bg-white border border-slate-200 shadow-xl rounded-xl p-4 w-80 relative flex gap-3">
            <button
              onClick={clearAlert}
              className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
            <div className={`p-2 rounded-full h-fit shrink-0 ${
              lastAlert.level === "success" ? "bg-primary/10 text-primary" :
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

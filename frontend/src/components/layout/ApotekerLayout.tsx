import { useState } from "react"
import { Navigate, Outlet, Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { useWebSocket } from "../../hooks/useWebSocket"
import NotificationDropdown from "../NotificationDropdown"
import {
  LogOut, LayoutDashboard, ClipboardList, Package, X, FileText, Bell
} from "lucide-react"

export default function ApotekerLayout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const location = useLocation()
  const { lastAlert, clearAlert } = useWebSocket()

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
    { to: "/apoteker/stok", label: "Kelola Stok Batch", icon: ClipboardList },
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
            <div className="flex items-center">
              <NotificationDropdown />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

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

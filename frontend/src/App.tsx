import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import PublicLayout from "./components/layout/PublicLayout"
import ProtectedLayout from "./components/layout/ProtectedLayout"
import PosLayout from "./components/layout/PosLayout"
import LoginPage from "./pages/auth/LoginPage"
import CatalogPage from "./pages/public/CatalogPage"
import DashboardPage from "./pages/dashboard/DashboardPage"
import AdminProductsPage from "./pages/dashboard/AdminProductsPage"
import AdminUsersPage from "./pages/dashboard/AdminUsersPage"
import AdminAuditLogPage from "./pages/dashboard/AdminAuditLogPage"
import AdminSettingsPage from "./pages/dashboard/AdminSettingsPage"
import PosPage from "./pages/pos/PosPage"
import ApotekerLayout from "./components/layout/ApotekerLayout"
import ApotekerDashboardPage from "./pages/apoteker/ApotekerDashboardPage"
import ApotekerVerifikasiPage from "./pages/apoteker/ApotekerVerifikasiPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Navigate to="/catalog" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
        </Route>
        {/* POS Routes (Kasir / Admin) */}
        <Route element={<PosLayout />}>
          <Route path="/pos" element={<PosPage />} />
        </Route>

        {/* Apoteker Routes */}
        <Route element={<ApotekerLayout />}>
          <Route path="/apoteker" element={<ApotekerDashboardPage />} />
          <Route path="/apoteker/verifikasi" element={<ApotekerVerifikasiPage />} />
          <Route path="/apoteker/produk" element={<AdminProductsPage />} />
        </Route>
        
        {/* Protected Routes (Dashboard) */}
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/admin/products" element={<AdminProductsPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/audit" element={<AdminAuditLogPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

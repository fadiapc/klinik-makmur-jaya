import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import PublicLayout from "./components/layout/PublicLayout"
import ProtectedLayout from "./components/layout/ProtectedLayout"
import LoginPage from "./pages/auth/LoginPage"
import CatalogPage from "./pages/public/CatalogPage"
import DashboardPage from "./pages/dashboard/DashboardPage"
import AdminProductsPage from "./pages/dashboard/AdminProductsPage"
import AdminUsersPage from "./pages/dashboard/AdminUsersPage"

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
        
        {/* Protected Routes (Dashboard) */}
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/admin/products" element={<AdminProductsPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

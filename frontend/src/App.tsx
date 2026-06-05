import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import React from "react"
import PublicLayout from "./components/layout/PublicLayout"
import ProtectedLayout from "./components/layout/ProtectedLayout"
import PosLayout from "./components/layout/PosLayout"
import CustomerLayout from "./components/layout/CustomerLayout"
import LoginPage from "./pages/auth/LoginPage"
import RegisterPage from "./pages/auth/RegisterPage"
import CatalogPage from "./pages/public/CatalogPage"
import ProductDetailPage from "./pages/public/ProductDetailPage"
import CartPage from "./pages/customer/CartPage"
import CheckoutPage from "./pages/customer/CheckoutPage"
import OrderHistoryPage from "./pages/customer/OrderHistoryPage"
import DashboardPage from "./pages/dashboard/DashboardPage"
import AdminProductsPage from "./pages/dashboard/AdminProductsPage"
import AdminUsersPage from "./pages/dashboard/AdminUsersPage"
import AdminAuditLogPage from "./pages/dashboard/AdminAuditLogPage"
import PosPage from "./pages/pos/PosPage"
import ApotekerLayout from "./components/layout/ApotekerLayout"
import ApotekerDashboardPage from "./pages/apoteker/ApotekerDashboardPage"
import ApotekerVerifikasiPage from "./pages/apoteker/ApotekerVerifikasiPage"

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: any}> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "20px", color: "red", fontFamily: "monospace" }}>
          <h2>React Render Error</h2>
          <pre>{this.state.error?.toString()}</pre>
          <pre>{this.state.error?.stack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Navigate to="/catalog" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/catalog/:id" element={<ProductDetailPage />} />
          </Route>
          
          {/* Customer Routes (Pasien) */}
          <Route element={<CustomerLayout />}>
            <Route path="/cart" element={<CartPage />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/orders" element={<OrderHistoryPage />} />
          </Route>
          
          {/* Protected Routes (Admin) */}
          <Route element={<ProtectedLayout />}>
            <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="/admin/dashboard" element={<DashboardPage />} />
            <Route path="/admin/products" element={<AdminProductsPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/audit" element={<AdminAuditLogPage />} />
          </Route>

          {/* POS Routes (Kasir) */}
          <Route element={<PosLayout />}>
            <Route path="/pos" element={<PosPage />} />
          </Route>

          {/* Apoteker Routes */}
          <Route element={<ApotekerLayout />}>
            <Route path="/apoteker" element={<ApotekerDashboardPage />} />
            <Route path="/apoteker/verifikasi/:id" element={<ApotekerVerifikasiPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

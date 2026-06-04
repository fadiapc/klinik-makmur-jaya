import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import PublicLayout from "./components/layout/PublicLayout"
import ProtectedLayout from "./components/layout/ProtectedLayout"
import LoginPage from "./pages/auth/LoginPage"
import CatalogPage from "./pages/public/CatalogPage"

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
        
        {/* Protected Routes */}
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={
            <div className="p-8">
              <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
              <p className="text-muted-foreground mt-2">Welcome to Makmur Jaya E-Commerce System</p>
            </div>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

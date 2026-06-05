import React, { useState } from "react"
import { useNavigate, Navigate, Link } from "react-router-dom"
import { useAuthStore } from "../../store/authStore"
import { api } from "../../lib/api"
import { Loader2, Mail, Lock } from "lucide-react"

export default function LoginPage() {
  const [email, setEmail] = useState("admin@makmurjaya.com") // Seeded admin for demo
  const [password, setPassword] = useState("Admin123!")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAuthStore()

  // Redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      const response = await api.post("/auth/login", {
        email: email,
        password: password,
      })

      const { access_token, user } = response.data
      
      // Save to Zustand store
      login(access_token, user)
      
      // Navigate based on role
      if (user.role.name === "pasien") {
        navigate("/catalog")
      } else {
        navigate("/dashboard")
      }
    } catch (err: any) {
      let errorMsg = "Failed to connect to the server. Please ensure the backend is running."
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === "string") {
          errorMsg = err.response.data.detail
        } else if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map((e: any) => e.msg).join(", ")
        } else {
          errorMsg = JSON.stringify(err.response.data.detail)
        }
      }
      setError(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="p-8 pb-6 text-center bg-slate-50 border-b border-slate-100">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Welcome Back</h1>
          <p className="text-slate-500 mt-2 text-sm">Sign in to your account to continue</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="p-8 space-y-5">
          {error && (
            <div className="p-3 rounded-md bg-red-50 text-red-600 text-sm font-medium border border-red-100">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail className="h-5 w-5" />
              </div>
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Password</label>
              <a href="#" className="text-sm text-teal-600 hover:text-teal-500 font-medium">Forgot password?</a>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 w-5" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-500 hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                Signing in...
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500">
          Belum punya akun?{" "}
          <Link to="/register" className="font-semibold text-teal-600 hover:text-teal-500 transition-colors">
            Daftar di sini
          </Link>
        </div>
      </div>
    </div>
  )
}

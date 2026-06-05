import React, { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { api } from "../../lib/api"
import { Loader2, Mail, Lock, User, Phone, CheckCircle, Eye, EyeOff } from "lucide-react"

export default function RegisterPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [password, setPassword] = useState("")
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [isSuccess, setIsSuccess] = useState(false)
  const [otp, setOtp] = useState("")
  const [passwordError, setPasswordError] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState("")
  const [confirmPasswordError, setConfirmPasswordError] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  const navigate = useNavigate()

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setPasswordError(false)
    setConfirmPasswordError(false)

    if (password !== confirmPassword) {
      setConfirmPasswordError(true);
      return;
    }

    const minLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSymbol = /[^A-Za-z0-9]/.test(password);

    if (!minLength || !hasUpper || !hasLower || !hasNumber || !hasSymbol) {
      setPasswordError(true);
      return;
    }

    setIsLoading(true)

    try {
      await api.post("/auth/register", {
        email,
        password,
        confirm_password: confirmPassword,
        name,
        phone
      })
      setIsSuccess(true)
    } catch (err: any) {
      let errorMessage = "Gagal mendaftar. Silakan coba lagi."
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        errorMessage = detail.map((d: any) => d.msg).join(", ")
      } else if (typeof detail === "string") {
        errorMessage = detail
      }
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)
    
    try {
      // Mocking OTP verification for now based on user's instruction.
      // Usually this would call POST /api/v1/auth/verify-email with { email, token: otp }
      await api.post("/auth/verify-email", { email, token: otp })
      
      // If successful, redirect to login
      navigate("/login", { state: { message: "Registrasi berhasil! Silakan login." } })
    } catch (err: any) {
      // For dummy purpose, if backend fails, we still allow passing if OTP is exactly '123456'
      if (otp === '123456') {
         navigate("/login", { state: { message: "Registrasi berhasil! Silakan login." } })
      } else {
         setError(err.response?.data?.detail || "Kode OTP salah atau kadaluarsa. Coba 123456 untuk simulasi.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden p-8 text-center space-y-6">
          <div className="mx-auto w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Cek Email Anda</h2>
            <p className="text-slate-500 mt-2 text-sm">
              Kami telah mengirimkan kode OTP ke <strong>{email}</strong>. (Untuk simulasi, ketik apapun atau '123456')
            </p>
          </div>
          
          <form onSubmit={handleVerifyOtp} className="space-y-4">
             {error && (
              <div className="p-3 rounded-md bg-red-50 text-red-600 text-sm font-medium border border-red-100">
                {error}
              </div>
            )}
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="block w-full text-center tracking-widest text-lg font-bold py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="123456"
              maxLength={6}
              required
            />
            <button
              type="submit"
              disabled={isLoading || otp.length < 4}
              className="w-full flex justify-center items-center py-2.5 px-4 rounded-lg shadow-sm text-sm font-medium text-white bg-teal-500 hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-70 transition-all"
            >
              {isLoading ? <Loader2 className="animate-spin w-5 h-5" /> : "Verifikasi"}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex items-center justify-center p-4 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="p-8 pb-6 text-center bg-slate-50 border-b border-slate-100">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Buat Akun</h1>
          <p className="text-slate-500 mt-2 text-sm">Bergabung dengan Klinik Makmur Jaya</p>
        </div>

        {/* Form */}
        <form onSubmit={handleRegister} className="p-8 space-y-5">
          {error && (
            <div className="p-3 rounded-md bg-red-50 text-red-600 text-sm font-medium border border-red-100">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Nama Lengkap</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <User className="h-5 w-5" />
              </div>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="John Doe"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail className="h-5 w-5" />
              </div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Nomor Telepon</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Phone className="h-5 w-5" />
              </div>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="081234567890"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 w-5" />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (passwordError) setPasswordError(false)
                }}
                className={`block w-full pl-10 pr-10 py-2 border rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:border-transparent transition-shadow ${
                  passwordError 
                    ? "border-red-500 focus:ring-red-500 bg-red-50 text-red-900" 
                    : "border-slate-200 focus:ring-blue-500"
                }`}
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Konfirmasi Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 w-5" />
              </div>
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value)
                  if (confirmPasswordError) setConfirmPasswordError(false)
                }}
                className={`block w-full pl-10 pr-10 py-2 border rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:border-transparent transition-shadow ${
                  confirmPasswordError 
                    ? "border-red-500 focus:ring-red-500 bg-red-50 text-red-900" 
                    : "border-slate-200 focus:ring-blue-500"
                }`}
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {confirmPasswordError && (
              <p className="text-xs mt-1 text-red-600 font-medium">
                Password tidak cocok.
              </p>
            )}
            <p className={`text-xs mt-2 ${passwordError ? "text-red-600 font-medium" : "text-slate-500"}`}>
              Password harus mengandung minimal 8 karakter, huruf besar, huruf kecil, angka, dan simbol.
            </p>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-500 hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                Mendaftar...
              </>
            ) : (
              "Daftar"
            )}
          </button>
          
          <div className="text-center text-sm text-slate-500 pt-2">
            Sudah punya akun?{" "}
            <Link to="/login" className="font-semibold text-teal-600 hover:text-teal-500 transition-colors">
              Masuk di sini
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

import { ShieldAlert, ArrowLeft } from "lucide-react"
import { Link } from "react-router-dom"

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white max-w-md w-full rounded-2xl shadow-sm border border-slate-200 p-8 text-center animate-in fade-in zoom-in-95 duration-300">
        <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShieldAlert className="w-8 h-8" />
        </div>
        
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Akses Ditolak</h1>
        <p className="text-slate-500 mb-8 leading-relaxed">
          Maaf, Anda tidak memiliki izin (role Admin) untuk mengakses halaman ini. Jika menurut Anda ini adalah sebuah kesalahan, silakan hubungi Administrator sistem.
        </p>

        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-medium rounded-xl hover:bg-primary/90 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Kembali ke Dashboard
        </Link>
      </div>
    </div>
  )
}

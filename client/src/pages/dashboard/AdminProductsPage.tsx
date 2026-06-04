import { Plus } from "lucide-react"

export default function AdminProductsPage() {
  return (
    <div className="p-8 space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Kelola Produk</h1>
          <p className="text-muted-foreground mt-1">Manajemen inventori obat dan alat kesehatan.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors shadow-sm font-medium">
          <Plus className="w-4 h-4" />
          Tambah Produk
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50">
          <input 
            type="text" 
            placeholder="Cari produk..." 
            className="w-full max-w-sm px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-shadow"
          />
        </div>
        
        <div className="p-12 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl text-slate-400">📦</span>
          </div>
          <h3 className="text-lg font-medium text-slate-900">Belum Ada Data</h3>
          <p className="text-slate-500 mt-1 max-w-sm">
            Saat ini tabel produk masih dalam tahap pengembangan. Segera Anda dapat mengelola produk dari halaman ini.
          </p>
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect } from "react"
import { api } from "../../lib/api"
import { Search, Filter, Loader2, Info } from "lucide-react"

export default function CatalogPage() {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async (search) => {
    setIsLoading(true)
    setError("")
    try {
      const url = search ? `/products?q=${search}` : `/products`
      const response = await api.get(url)
      setData(response.data)
    } catch (err) {
      setError("Gagal memuat data katalog. Pastikan server backend berjalan.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    fetchProducts(searchQuery)
  }

  const formatIDR = (price) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(parseFloat(price))
  }

  const getImageUrl = (url) => {
    if (!url) return "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&q=80"
    return `http://localhost:8000/static/${url}`
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Katalog Obat</h1>
          <p className="text-slate-500 mt-2">Cari dan pesan obat sesuai kebutuhan medis Anda.</p>
        </div>
        
        <div className="w-full md:w-96 flex gap-2">
          <form onSubmit={handleSearch} className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              placeholder="Cari nama, SKU..."
            />
          </form>
          <button className="p-2 border border-slate-200 rounded-lg text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* State Handling */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 text-red-600 border border-red-100 flex items-center gap-3">
          <Info className="w-5 h-5" />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center items-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : (
        /* Product Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {data?.items.map((product) => (
            <div 
              key={product.id} 
              className="group bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-xl hover:border-slate-200 transition-all duration-300 flex flex-col"
            >
              {/* Image Container */}
              <div className="aspect-[4/3] bg-slate-100 relative overflow-hidden">
                <img 
                  src={getImageUrl(product.image_url)} 
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                {product.requires_prescription && (
                  <span className="absolute top-3 right-3 bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-sm tracking-wide">
                    RESEP DOKTER
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="p-5 flex flex-col flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                    {product.category_name}
                  </span>
                  <span className="text-xs text-slate-400">{product.sku}</span>
                </div>
                
                <h3 className="font-semibold text-slate-900 line-clamp-1 mb-1 group-hover:text-blue-600 transition-colors">
                  {product.name}
                </h3>
                
                <p className="text-sm text-slate-500 line-clamp-2 mb-4 flex-1">
                  {product.description || "Tidak ada deskripsi tersedia."}
                </p>
                
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100">
                  <span className="text-lg font-bold text-slate-900">
                    {formatIDR(product.price)}
                  </span>
                  <button className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-600 hover:bg-blue-600 hover:text-white transition-colors">
                    +
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && data?.items.length === 0 && (
        <div className="text-center py-32">
          <div className="inline-flex w-16 h-16 rounded-full bg-slate-50 items-center justify-center mb-4">
            <Search className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900">Tidak ada obat ditemukan</h3>
          <p className="text-slate-500 mt-1">Coba gunakan kata kunci pencarian yang lain.</p>
        </div>
      )}
    </div>
  )
}

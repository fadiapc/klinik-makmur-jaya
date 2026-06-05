import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../../lib/api"
import { useAuthStore } from "../../store/authStore"
import { useCartStore } from "../../store/cartStore"
import { Search, Loader2, Info, ShoppingCart, CheckCircle, AlertTriangle } from "lucide-react"

interface Product {
  id: number
  sku: string
  name: string
  description: string | null
  price: string
  requires_prescription: boolean
  image_url: string | null
  category: { id: number; name: string }
  supplier: { id: number; name: string }
}

interface Category {
  id: number
  name: string
}

interface PaginatedResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export default function CatalogPage() {
  const [data, setData] = useState<PaginatedResponse | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [sortOption, setSortOption] = useState<string>("")
  const [addedItem, setAddedItem] = useState<number | null>(null) // For success feedback

  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const { addItem } = useCartStore()

  useEffect(() => {
    fetchCategories()
    fetchProducts()
  }, [])

  useEffect(() => {
    fetchProducts()
  }, [selectedCategory, sortOption])

  const fetchCategories = async () => {
    try {
      const res = await api.get("/products/categories")
      setCategories(res.data)
    } catch (err) {
      console.error("Gagal memuat kategori", err)
    }
  }

  const fetchProducts = async (search?: string) => {
    setIsLoading(true)
    setError("")
    try {
      const params = new URLSearchParams()
      if (search || searchQuery) params.set("q", search ?? searchQuery)
      if (selectedCategory) params.set("category_id", String(selectedCategory))
      if (sortOption === "price_asc") {
        params.set("sort_by", "price")
        params.set("sort_order", "asc")
      } else if (sortOption === "price_desc") {
        params.set("sort_by", "price")
        params.set("sort_order", "desc")
      }

      const queryString = params.toString()
      const url = queryString ? `/products?${queryString}` : `/products`
      
      const response = await api.get(url)
      setData(response.data)
    } catch (err: any) {
      console.error("API Error in fetchProducts:", err)
      const errorMsg = err.response?.data?.detail || err.message || "Pastikan server backend berjalan."
      setError(`Gagal memuat data katalog. Detail: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchProducts()
  }

  const handleAddToCart = (product: Product) => {
    if (!isAuthenticated) {
      navigate("/login", { state: { message: "Silakan login untuk menambahkan ke keranjang" } })
      return
    }
    addItem(product, 1)
    
    // Show feedback
    setAddedItem(product.id)
    setTimeout(() => setAddedItem(null), 2000)
  }

  const formatIDR = (price: string) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(parseFloat(price))
  }

  const getImageUrl = (url: string | null) => {
    if (!url) return "https://placehold.co/400x400/f8fafc/94a3b8?text=No+Image"
    return `http://localhost:8000/static/${url}`
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-[1400px]">
      
      {/* Top Header / Search / Filter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Katalog Produk</h1>
          <p className="text-slate-500 text-sm mt-1">Temukan obat dan kebutuhan medis Anda.</p>
        </div>
        
        <div className="w-full md:w-auto flex-1 max-w-4xl">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-2">
            
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="block w-full md:w-40 pl-3 pr-8 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white"
            >
              <option value="">Urutkan</option>
              <option value="price_asc">Harga Terendah</option>
              <option value="price_desc">Harga Tertinggi</option>
            </select>

            <select
              value={selectedCategory === null ? "" : selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
              className="block w-full sm:w-48 pl-3 pr-8 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white"
            >
              <option value="">Semua Kategori</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>

            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="h-5 w-5" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                placeholder="Cari produk & obat di sini..."
              />
            </div>
            
            <button 
              type="submit"
              className="bg-teal-500 hover:bg-teal-600 text-white px-6 py-3 rounded-xl font-bold transition-colors shadow-sm flex-shrink-0"
            >
              Cari
            </button>
          </form>
        </div>
      </div>

      <div className="flex flex-col gap-8">
        
        {/* Main Content - Product Grid */}
        <div className="flex-1 w-full">
          {error && (
            <div className="p-4 rounded-xl bg-red-50 text-red-600 border border-red-100 flex items-center gap-3 mb-6">
              <Info className="w-5 h-5" />
              {error}
            </div>
          )}

          {/* Result Info */}
          {!isLoading && data && (
            <div className="flex items-center justify-between mb-6">
              <p className="text-slate-500 text-sm">
                Menampilkan <span className="font-semibold text-slate-900">{data.items.length}</span> produk dari total <span className="font-semibold text-slate-900">{data.total}</span>
              </p>
            </div>
          )}

          {isLoading ? (
            <div className="flex flex-col justify-center items-center py-32 space-y-4">
              <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
              <p className="text-slate-500 animate-pulse">Memuat katalog produk...</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
              {data?.items.map((product) => (
                <div 
                  key={product.id} 
                  className="group bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm hover:shadow-lg hover:border-blue-200 transition-all duration-300 flex flex-col cursor-pointer"
                  onClick={() => navigate(`/catalog/${product.id}`)}
                >
                  {/* Image Container */}
                  <div className="aspect-square bg-white relative overflow-hidden p-4">
                    <img 
                      src={getImageUrl(product.image_url)} 
                      alt={product.name}
                      className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-500"
                    />
                    {product.requires_prescription && (
                      <span className="absolute top-3 right-3 bg-red-100 text-red-700 border border-red-200 text-[10px] font-bold px-2 py-1 rounded-full shadow-sm tracking-wide flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        RESEP DOKTER
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4 flex flex-col flex-1 border-t border-slate-50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded">
                        {product.category.name}
                      </span>
                    </div>
                    
                    <h3 className="font-bold text-slate-900 line-clamp-2 mb-2 group-hover:text-teal-600 transition-colors text-base leading-snug flex-1">
                      {product.name}
                    </h3>
                    
                    <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <span className="block text-lg font-bold text-slate-900">
                        {formatIDR(product.price)}
                      </span>
                      
                      <button 
                        onClick={(e) => {
                          e.stopPropagation(); // Prevent navigating to detail page
                          handleAddToCart(product);
                        }}
                        disabled={addedItem === product.id}
                        title="Tambah ke Keranjang"
                        className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                          addedItem === product.id 
                            ? "bg-green-100 text-green-700 border border-green-200" 
                            : "bg-teal-500 hover:bg-teal-600 text-white shadow-sm hover:shadow-md"
                        }`}
                      >
                        {addedItem === product.id ? (
                          <CheckCircle className="w-5 h-5" />
                        ) : (
                          <ShoppingCart className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && data?.items.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
              <div className="inline-flex w-20 h-20 rounded-full bg-slate-50 items-center justify-center mb-4 border border-slate-100">
                <Search className="w-10 h-10 text-slate-400" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Tidak ada produk ditemukan</h3>
              <p className="text-slate-500 mt-2 max-w-md mx-auto">Kami tidak dapat menemukan produk yang sesuai dengan pencarian atau filter Anda. Coba gunakan kata kunci lain.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

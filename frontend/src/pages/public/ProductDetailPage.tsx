import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { api } from "../../lib/api"
import { useAuthStore } from "../../store/authStore"
import { useCartStore } from "../../store/cartStore"
import { Loader2, ArrowLeft, ShieldAlert, ShoppingCart, Info, Activity, AlertTriangle } from "lucide-react"

interface Product {
  id: number
  sku: string
  name: string
  description: string | null
  composition: string | null
  dosage: string | null
  side_effects: string | null
  price: string
  requires_prescription: boolean
  image_url: string | null
  category: { id: number; name: string }
  supplier: { id: number; name: string }
}

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [product, setProduct] = useState<Product | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  
  const [quantity, setQuantity] = useState(1)
  const [isAdding, setIsAdding] = useState(false)

  const { isAuthenticated } = useAuthStore()
  const { addItem } = useCartStore()

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const res = await api.get(`/products/${id}`)
        setProduct(res.data)
      } catch (err: any) {
        setError(err.response?.data?.detail || "Gagal memuat detail produk.")
      } finally {
        setIsLoading(false)
      }
    }
    fetchProduct()
  }, [id])

  const handleAddToCart = () => {
    if (!product) return
    
    if (!isAuthenticated) {
      navigate("/login", { state: { message: "Silakan login untuk menambahkan ke keranjang" } })
      return
    }

    setIsAdding(true)
    addItem(product, quantity)
    setTimeout(() => {
      setIsAdding(false)
      navigate("/catalog") // Or you can keep them here and show a toast
    }, 600)
  }

  const formatIDR = (price: string) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(parseFloat(price))
  }

  const getImageUrl = (url: string | null) => {
    if (!url) return "https://placehold.co/600x600/f8fafc/94a3b8?text=No+Image"
    return `http://localhost:8000/static/${url}`
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-32">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="container mx-auto px-4 py-16 text-center max-w-2xl">
        <div className="bg-red-50 text-red-600 p-8 rounded-2xl border border-red-100">
          <Info className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h2 className="text-xl font-bold mb-2">Produk Tidak Ditemukan</h2>
          <p>{error}</p>
          <button 
            onClick={() => navigate("/catalog")}
            className="mt-6 bg-red-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors"
          >
            Kembali ke Katalog
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <button 
        onClick={() => navigate("/catalog")}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-900 font-medium mb-8 transition-colors w-fit"
      >
        <ArrowLeft className="w-5 h-5" />
        Kembali ke Katalog
      </button>

      <div className="bg-white rounded-3xl p-6 md:p-10 shadow-sm border border-slate-200">
        <div className="flex flex-col lg:flex-row gap-10 lg:gap-16">
          
          {/* Image Section */}
          <div className="w-full lg:w-5/12 flex-shrink-0">
            <div className="bg-slate-50 rounded-2xl p-8 border border-slate-100 aspect-square flex items-center justify-center relative overflow-hidden">
              <img 
                src={getImageUrl(product.image_url)} 
                alt={product.name}
                className="w-full h-full object-contain"
              />
              {product.requires_prescription && (
                <div className="absolute top-4 right-4 bg-red-100 text-red-700 border border-red-200 text-xs font-bold px-3 py-1.5 rounded-full shadow-sm flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  WAJIB RESEP DOKTER
                </div>
              )}
            </div>
          </div>

          {/* Details Section */}
          <div className="flex-1 flex flex-col">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-sm font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-3 py-1 rounded-md">
                  {product.category.name}
                </span>
                <span className="text-sm text-slate-500">SKU: {product.sku}</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">{product.name}</h1>
              <p className="text-3xl font-extrabold text-teal-600 mb-6">
                {formatIDR(product.price)}
              </p>
            </div>

            <div className="space-y-6 flex-1">
              {/* Add to Cart Box */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-4">
                <div className="flex items-center bg-white border border-slate-300 rounded-xl overflow-hidden w-full sm:w-auto">
                  <button 
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="w-12 h-12 flex justify-center items-center text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors text-lg"
                  >
                    -
                  </button>
                  <input 
                    type="number" 
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-16 h-12 text-center border-x border-slate-300 font-bold focus:outline-none"
                    min="1"
                  />
                  <button 
                    onClick={() => setQuantity(quantity + 1)}
                    className="w-12 h-12 flex justify-center items-center text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors text-lg"
                  >
                    +
                  </button>
                </div>
                
                <button 
                  onClick={handleAddToCart}
                  disabled={isAdding}
                  className="flex-1 w-full bg-teal-500 hover:bg-teal-600 disabled:opacity-70 text-white h-12 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all shadow-sm hover:shadow"
                >
                  {isAdding ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <ShoppingCart className="w-5 h-5" />
                      Tambah ke Keranjang
                    </>
                  )}
                </button>
              </div>

              {/* Product Info Tabs / Sections */}
              <div className="space-y-6 pt-6 border-t border-slate-100">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-2">
                    <Info className="w-5 h-5 text-blue-500" />
                    Deskripsi Produk
                  </h3>
                  <p className="text-slate-600 leading-relaxed text-sm md:text-base">
                    {product.description || "Tidak ada deskripsi yang tersedia untuk produk ini."}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {product.composition && (
                    <div className="bg-blue-50/50 rounded-xl p-4 border border-blue-100/50">
                      <h4 className="font-bold text-slate-900 text-sm mb-1">Komposisi</h4>
                      <p className="text-slate-600 text-sm leading-relaxed">{product.composition}</p>
                    </div>
                  )}
                  {product.dosage && (
                    <div className="bg-emerald-50/50 rounded-xl p-4 border border-emerald-100/50">
                      <h4 className="font-bold text-slate-900 text-sm mb-1 flex items-center gap-1.5">
                        <Activity className="w-4 h-4 text-emerald-600" />
                        Dosis & Aturan Pakai
                      </h4>
                      <p className="text-slate-600 text-sm leading-relaxed">{product.dosage}</p>
                    </div>
                  )}
                </div>

                {product.side_effects && (
                  <div className="bg-amber-50/50 rounded-xl p-4 border border-amber-100/50">
                    <h4 className="font-bold text-amber-900 text-sm mb-1 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Efek Samping
                    </h4>
                    <p className="text-amber-700/80 text-sm leading-relaxed">{product.side_effects}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

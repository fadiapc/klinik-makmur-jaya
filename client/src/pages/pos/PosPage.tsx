import { useState, useEffect, useMemo } from "react"
import { Search, Plus, Minus, Trash2, ShoppingCart, Loader2 } from "lucide-react"
import { getProducts } from "../../services/productService"
import type { Product } from "../../services/productService"
import { api } from "../../lib/api"

interface CartItem {
  product: Product
  quantity: number
}

export default function PosPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  
  // Cart State
  const [cart, setCart] = useState<CartItem[]>([])
  const [paymentMethod, setPaymentMethod] = useState("cash")
  const [isProcessing, setIsProcessing] = useState(false)
  const [cashReceived, setCashReceived] = useState<number | "">("")

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      setLoading(true)
      const res = await getProducts({ page: 1, limit: 100 }) // fetch up to 100 products for POS
      setProducts(res.items.filter(p => p.is_active))
    } catch (error) {
      console.error(error)
      alert("Gagal memuat daftar obat")
    } finally {
      setLoading(false)
    }
  }

  // Derived State: Fuzzy Search & Filter
  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchesSearch = 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        p.sku.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesCategory = 
        categoryFilter === "all" || p.category.name.toLowerCase() === categoryFilter.toLowerCase()

      return matchesSearch && matchesCategory
    })
  }, [products, searchQuery, categoryFilter])

  // Cart Functions
  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id)
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        )
      }
      return [...prev, { product, quantity: 1 }]
    })
  }

  const updateQuantity = (productId: number, delta: number) => {
    setCart((prev) => {
      return prev.map((item) => {
        if (item.product.id === productId) {
          const newQty = item.quantity + delta
          return newQty > 0 ? { ...item, quantity: newQty } : item
        }
        return item
      })
    })
  }

  const removeFromCart = (productId: number) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId))
  }

  // Calculations
  const subtotal = cart.reduce((sum, item) => sum + Number(item.product.price) * item.quantity, 0)
  const tax = subtotal * 0.11 // PPN 11%
  const grandTotal = subtotal + tax

  // Checkout
  const handleCheckout = async () => {
    if (cart.length === 0) return

    setIsProcessing(true)
    try {
      const payload = {
        items: cart.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity
        })),
        payment_method: paymentMethod
      }

      const response = await api.post("/orders/checkout", payload)
      
      alert(`Pesanan berhasil diproses! Kode: ${response.data.order_code}`)
      setCart([]) // Reset cart
      setCashReceived("") // Reset cash
      
    } catch (error: any) {
      console.error(error)
      alert(error.response?.data?.detail || "Gagal memproses pesanan")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="flex h-full bg-slate-100/50 overflow-hidden">
      
      {/* Left Column: Product Catalog (70%) */}
      <div className="flex-1 flex flex-col h-full border-r border-slate-200 bg-slate-50/50">
        
        {/* Search & Filter Header */}
        <div className="h-16 bg-white border-b shadow-sm z-10 shrink-0 px-6 flex items-center">
          <div className="flex w-full gap-4 items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                <input 
                  type="text" 
                  placeholder="Cari nama atau kode obat..." 
                  className="w-full pl-9 pr-4 py-2 bg-slate-100 border-transparent focus:bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <select 
                className="px-3 py-2 bg-slate-100 border-transparent rounded-lg text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all cursor-pointer hover:bg-slate-200 shrink-0"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="all">Semua Kategori</option>
                <option value="bebas">Obat Bebas</option>
                <option value="resep">Obat Resep</option>
                <option value="suplemen">Suplemen</option>
                <option value="alkes">Alkes</option>
              </select>
            </div>
          </div>

        {/* Product Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex h-full items-center justify-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
              <Search className="w-12 h-12 opacity-20" />
              <p>Tidak ada produk yang cocok dengan pencarian.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in duration-500">
              {filteredProducts.map((product) => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-primary/30 transition-all text-left flex flex-col gap-3 group relative overflow-hidden"
                >
                  <div className="flex justify-between items-start w-full gap-2">
                    <span className="px-2.5 py-1 bg-blue-50 text-blue-600 rounded-md text-xs font-medium border border-blue-100">
                      {product.category.name}
                    </span>
                    {/* Mocked stock, as current_stock isn't exposed yet */}
                    <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded">
                      Sisa: 99
                    </span>
                  </div>
                  
                  <div>
                    <h3 className="font-bold text-slate-800 line-clamp-2 leading-snug group-hover:text-primary transition-colors">
                      {product.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">{product.sku}</p>
                  </div>
                  
                  <div className="mt-auto pt-2">
                    <p className="text-lg font-bold text-emerald-600">
                      Rp {Number(product.price).toLocaleString("id-ID")}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>


      {/* Right Column: Cart (30%) */}
      <div className="w-96 bg-white flex flex-col shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] shrink-0 z-20">
        
        {/* Cart Header */}
        <div className="h-16 flex items-center justify-between px-6 bg-white border-b text-slate-800 shrink-0 shadow-sm z-10">
          <div className="flex items-center gap-3">
            <ShoppingCart className="w-5 h-5 text-primary" />
            <h2 className="font-bold text-lg">Keranjang Belanja</h2>
          </div>
          <span className="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-bold border border-primary/20">
            {cart.reduce((acc, item) => acc + item.quantity, 0)} Item
          </span>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50">
          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
              <ShoppingCart className="w-12 h-12 opacity-20" />
              <p className="text-sm">Keranjang masih kosong</p>
            </div>
          ) : (
            cart.map((item) => (
              <div key={item.product.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3 animate-in slide-in-from-right-2 duration-200">
                <div className="flex justify-between items-start gap-2">
                  <h4 className="font-bold text-sm text-slate-800 leading-tight">
                    {item.product.name}
                  </h4>
                  <button 
                    onClick={() => removeFromCart(item.product.id)}
                    className="text-slate-400 hover:text-red-500 transition-colors p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="flex justify-between items-center mt-1">
                  <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5 border border-slate-200">
                    <button 
                      onClick={() => updateQuantity(item.product.id, -1)}
                      className="p-1 hover:bg-white rounded-md text-slate-600 transition-colors shadow-sm"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="w-8 text-center text-sm font-semibold text-slate-800">
                      {item.quantity}
                    </span>
                    <button 
                      onClick={() => updateQuantity(item.product.id, 1)}
                      className="p-1 hover:bg-white rounded-md text-slate-600 transition-colors shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  
                  <p className="font-bold text-slate-800 text-sm">
                    Rp {(Number(item.product.price) * item.quantity).toLocaleString("id-ID")}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Checkout Footer */}
        <div className="bg-white border-t border-slate-200 p-5 shrink-0">
          
          <div className="space-y-2 text-sm text-slate-600 mb-4">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span className="font-medium text-slate-800">Rp {subtotal.toLocaleString("id-ID")}</span>
            </div>
            <div className="flex justify-between">
              <span>Pajak (PPN 11%)</span>
              <span className="font-medium text-slate-800">Rp {tax.toLocaleString("id-ID")}</span>
            </div>
            
            <hr className="border-slate-100 my-2" />
            
            <div className="flex justify-between items-center pt-1">
              <span className="font-bold text-slate-900 text-base">Total Bayar</span>
              <span className="font-black text-emerald-600 text-xl">Rp {grandTotal.toLocaleString("id-ID")}</span>
            </div>
          </div>

          <div className="mb-4">
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">Metode Pembayaran</label>
            <select 
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary font-medium text-sm"
              value={paymentMethod}
              onChange={(e) => {
                setPaymentMethod(e.target.value)
                if (e.target.value !== "cash") setCashReceived("")
              }}
            >
              <option value="cash">Tunai (Cash)</option>
              <option value="transfer">Transfer Bank</option>
              <option value="qris">QRIS</option>
            </select>
          </div>

          {paymentMethod === "cash" && (
            <div className="mb-4 space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">Uang Tunai Diterima</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-medium text-sm">Rp</span>
                  <input 
                    type="number" 
                    placeholder="0"
                    min="0"
                    className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary font-medium text-sm"
                    value={cashReceived}
                    onChange={(e) => setCashReceived(e.target.value ? Number(e.target.value) : "")}
                  />
                </div>
              </div>
              
              {cashReceived !== "" && cashReceived >= grandTotal && (
                <div className="flex justify-between items-center bg-emerald-50 text-emerald-700 px-3 py-2 rounded-lg border border-emerald-100">
                  <span className="font-semibold text-sm">Kembalian:</span>
                  <span className="font-bold">Rp {(Number(cashReceived) - grandTotal).toLocaleString("id-ID")}</span>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <button 
              onClick={handleCheckout}
              disabled={cart.length === 0 || isProcessing || (paymentMethod === "cash" && (cashReceived === "" || cashReceived < grandTotal))}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl shadow-md shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {isProcessing ? "MEMPROSES..." : "KONFIRMASI PEMBAYARAN"}
            </button>
          </div>

        </div>
      </div>
      
    </div>
  )
}

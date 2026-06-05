import { useNavigate } from "react"
import { useCartStore } from "../../store/cartStore"
import { Trash2, AlertTriangle, ArrowRight, ArrowLeft } from "lucide-react"

export default function CartPage() {
  const { items, updateQuantity, removeItem, totalPrice } = useCartStore()
  const navigate = useNavigate()

  const formatIDR = (price: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(price)
  }

  const getImageUrl = (url: string | null) => {
    if (!url) return "https://placehold.co/400x400/f8fafc/94a3b8?text=No+Image"
    return `http://localhost:8000/static/${url}`
  }

  const hasPrescriptionItems = items.some(item => item.requires_prescription)

  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center max-w-2xl">
        <div className="bg-white p-12 rounded-3xl border border-slate-200 shadow-sm">
          <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Keranjang Anda Kosong</h2>
          <p className="text-slate-500 mb-8">Belum ada produk yang ditambahkan ke keranjang belanja Anda.</p>
          <button 
            onClick={() => navigate("/catalog")}
            className="inline-flex items-center justify-center rounded-xl font-bold transition-all bg-blue-600 text-white hover:bg-blue-700 h-12 px-8 shadow-sm"
          >
            Mulai Belanja
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={() => navigate("/catalog")}
          className="p-2 hover:bg-slate-200 rounded-full transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Keranjang Belanja</h1>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Cart Items */}
        <div className="flex-1 space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex gap-4">
              <div className="w-24 h-24 bg-slate-50 rounded-xl overflow-hidden border border-slate-100 flex-shrink-0">
                <img src={getImageUrl(item.image_url)} alt={item.name} className="w-full h-full object-contain p-2" />
              </div>
              
              <div className="flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start gap-4">
                    <h3 className="font-bold text-slate-900 line-clamp-2">{item.name}</h3>
                    <button 
                      onClick={() => removeItem(item.id)}
                      className="text-red-400 hover:text-red-600 p-1"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                  {item.requires_prescription && (
                    <span className="inline-flex items-center gap-1 mt-1 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-md border border-red-100">
                      <AlertTriangle className="w-3 h-3" />
                      RESEP DOKTER
                    </span>
                  )}
                </div>

                <div className="flex items-end justify-between mt-4">
                  <div className="font-bold text-slate-900">
                    {formatIDR(parseFloat(item.price))}
                  </div>
                  
                  <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden h-9">
                    <button 
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      className="w-8 h-full flex justify-center items-center text-slate-600 hover:bg-slate-100 transition-colors"
                    >
                      -
                    </button>
                    <input 
                      type="number" 
                      value={item.quantity}
                      onChange={(e) => updateQuantity(item.id, parseInt(e.target.value) || 1)}
                      className="w-10 h-full text-center border-x border-slate-300 font-medium text-sm focus:outline-none"
                      min="1"
                    />
                    <button 
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      className="w-8 h-full flex justify-center items-center text-slate-600 hover:bg-slate-100 transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="w-full lg:w-80 flex-shrink-0">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sticky top-24">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Ringkasan Pesanan</h2>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-slate-600">
                <span>Total Harga ({items.reduce((acc, item) => acc + item.quantity, 0)} barang)</span>
                <span className="font-medium text-slate-900">{formatIDR(totalPrice())}</span>
              </div>
              <div className="pt-4 border-t border-slate-100 flex justify-between">
                <span className="font-bold text-slate-900">Total Tagihan</span>
                <span className="font-bold text-blue-600 text-lg">{formatIDR(totalPrice())}</span>
              </div>
            </div>

            {hasPrescriptionItems && (
              <div className="mb-6 bg-red-50 text-red-700 p-3 rounded-xl border border-red-100 flex gap-3 text-sm">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p>Keranjang Anda mengandung obat keras. Anda akan diminta untuk mengunggah resep dokter pada halaman selanjutnya.</p>
              </div>
            )}

            <button 
              onClick={() => navigate("/checkout")}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm"
            >
              Lanjut ke Pembayaran
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

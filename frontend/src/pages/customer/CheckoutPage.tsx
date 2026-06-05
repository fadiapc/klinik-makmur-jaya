import { useState, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "../../lib/api"
import { useCartStore } from "../../store/cartStore"
import { AlertTriangle, UploadCloud, FileImage, X, Loader2, ArrowLeft, CheckCircle } from "lucide-react"

export default function CheckoutPage() {
  const { items, totalPrice, clearCart } = useCartStore()
  const navigate = useNavigate()

  const [paymentMethod, setPaymentMethod] = useState("transfer")
  const [notes, setNotes] = useState("")
  
  const [prescriptionFile, setPrescriptionFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [successMode, setSuccessMode] = useState(false)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const safeItems = items || []
  const hasPrescriptionItems = safeItems.some(item => item.requires_prescription)

  const formatIDR = (price: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(price)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith("image/")) {
      setError("File resep harus berupa gambar (JPG, PNG).")
      return
    }

    setPrescriptionFile(file)
    const reader = new FileReader()
    reader.onload = (e) => setPreviewUrl(e.target?.result as string)
    reader.readAsDataURL(file)
    setError("")
  }

  const removeFile = () => {
    setPrescriptionFile(null)
    setPreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault()
    if (items.length === 0) return

    if (hasPrescriptionItems && !prescriptionFile) {
      setError("Silakan unggah foto resep dokter terlebih dahulu.")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      // 1. Create Order
      const payload = {
        items: items.map(item => ({ product_id: item.id, quantity: item.quantity })),
        payment_method: paymentMethod,
        notes: notes
      }
      
      const res = await api.post("/orders/checkout", payload)
      const order = res.data

      // 2. Upload Prescription if needed
      if (hasPrescriptionItems && order.prescription_required_and_missing && prescriptionFile) {
        const formData = new FormData()
        formData.append("file", prescriptionFile)
        
        await api.post(`/orders/${order.id}/prescription`, formData, {
          headers: { "Content-Type": "multipart/form-data" }
        })
      }

      setSuccessMode(true)
      clearCart()
      
      setTimeout(() => {
        navigate("/orders")
      }, 3000)

    } catch (err: any) {
      setError(err.response?.data?.detail || "Terjadi kesalahan saat memproses pesanan.")
      setIsLoading(false)
    }
  }

  if (safeItems.length === 0 && !successMode) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold mb-4">Keranjang Anda Kosong</h2>
        <button onClick={() => navigate("/catalog")} className="text-teal-600 font-medium">
          Kembali ke Katalog
        </button>
      </div>
    )
  }

  if (successMode) {
    return (
      <div className="container mx-auto px-4 py-24 text-center max-w-lg">
        <div className="bg-white p-10 rounded-3xl border border-slate-200 shadow-sm flex flex-col items-center">
          <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6">
            <CheckCircle className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Pesanan Berhasil Dibuat!</h2>
          <p className="text-slate-500 mb-8">
            Pesanan Anda sedang diproses. {hasPrescriptionItems && "Apoteker kami akan segera memverifikasi resep Anda."}
          </p>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 w-full animate-pulse rounded-full"></div>
          </div>
          <p className="text-xs text-slate-400 mt-4">Mengarahkan ke Riwayat Pesanan...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={() => navigate("/cart")}
          className="p-2 hover:bg-slate-200 rounded-full transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Checkout</h1>
      </div>

      <form onSubmit={handleCheckout} className="flex flex-col lg:flex-row gap-8">
        
        {/* Left Form */}
        <div className="flex-1 space-y-6">
          
          {error && (
            <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Prescription Upload */}
          {hasPrescriptionItems && (
            <div className="bg-white p-6 rounded-2xl border border-red-200 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <h2 className="text-lg font-bold text-slate-900">Unggah Resep Dokter</h2>
              </div>
              <p className="text-sm text-slate-600 mb-6">
                Pesanan Anda mengandung obat keras yang memerlukan resep dokter. Silakan unggah foto resep dokter Anda yang asli dan jelas.
              </p>

              {!prescriptionFile ? (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:bg-slate-50 hover:border-blue-400 transition-colors"
                >
                  <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-900 mb-1">Klik untuk unggah foto resep</p>
                  <p className="text-xs text-slate-500">Format: JPG, PNG (Max. 5MB)</p>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    accept="image/*" 
                    className="hidden" 
                  />
                </div>
              ) : (
                <div className="relative border border-slate-200 rounded-xl overflow-hidden group w-full max-w-sm">
                  <img src={previewUrl!} alt="Preview Resep" className="w-full h-48 object-cover" />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button 
                      type="button"
                      onClick={removeFile}
                      className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="absolute bottom-0 left-0 w-full bg-white/90 p-2 border-t flex items-center gap-2 text-sm">
                    <FileImage className="w-4 h-4 text-blue-600" />
                    <span className="truncate">{prescriptionFile.name}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Payment Method */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Metode Pembayaran</h2>
            <div className="space-y-3">
              <label className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${paymentMethod === 'transfer' ? 'border-teal-500 bg-teal-50' : 'border-slate-200 hover:border-teal-300'}`}>
                <input 
                  type="radio" 
                  name="payment" 
                  value="transfer" 
                  checked={paymentMethod === 'transfer'} 
                  onChange={() => setPaymentMethod('transfer')}
                  className="w-4 h-4 text-teal-600 border-slate-300 focus:ring-teal-500" 
                />
                <div className="flex-1">
                  <p className="font-bold text-slate-900 text-sm">Transfer Bank</p>
                  <p className="text-xs text-slate-500 mt-0.5">BCA, Mandiri, BNI, BRI</p>
                </div>
              </label>
              <label className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${paymentMethod === 'qris' ? 'border-teal-500 bg-teal-50' : 'border-slate-200 hover:border-teal-300'}`}>
                <input 
                  type="radio" 
                  name="payment" 
                  value="qris" 
                  checked={paymentMethod === 'qris'} 
                  onChange={() => setPaymentMethod('qris')}
                  className="w-4 h-4 text-teal-600 border-slate-300 focus:ring-teal-500" 
                />
                <div className="flex-1">
                  <p className="font-bold text-slate-900 text-sm">QRIS</p>
                  <p className="text-xs text-slate-500 mt-0.5">Gopay, OVO, Dana, LinkAja</p>
                </div>
              </label>
            </div>
          </div>

          {/* Notes */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Catatan Pesanan (Opsional)</h2>
            <textarea 
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Tambahkan catatan untuk pesanan Anda..."
              className="w-full p-4 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm h-24 resize-none"
            ></textarea>
          </div>
          
        </div>

        {/* Right Summary */}
        <div className="w-full lg:w-96 flex-shrink-0">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sticky top-24">
            <h2 className="text-lg font-bold text-slate-900 mb-4 border-b pb-4">Ringkasan</h2>
            
            <div className="space-y-4 mb-6">
              {safeItems.map((item) => (
                <div key={item.id} className="flex justify-between items-start gap-4">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900 line-clamp-2">{item.name}</p>
                    <p className="text-xs text-slate-500">{item.quantity} x {formatIDR(parseFloat(item.price))}</p>
                  </div>
                  <p className="text-sm font-bold text-slate-900 whitespace-nowrap">
                    {formatIDR(parseFloat(item.price) * item.quantity)}
                  </p>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-between mb-8">
              <span className="font-bold text-slate-900">Total Pembayaran</span>
              <span className="font-bold text-teal-600 text-xl">{formatIDR(totalPrice())}</span>
            </div>

            <button 
              type="submit"
              disabled={isLoading || (hasPrescriptionItems && !prescriptionFile)}
              className="w-full bg-teal-500 hover:bg-teal-600 text-white h-12 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Memproses...
                </>
              ) : (
                "Buat Pesanan"
              )}
            </button>
            <p className="text-[10px] text-center text-slate-500 mt-4 leading-relaxed">
              Dengan membuat pesanan, Anda menyetujui Syarat & Ketentuan yang berlaku.
            </p>
          </div>
        </div>

      </form>
    </div>
  )
}

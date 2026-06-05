import { useState, useEffect, useRef } from "react"
import { api } from "../../lib/api"
import { 
  Package, Clock, CheckCircle, XCircle, AlertTriangle, 
  ChevronRight, FileText, Wallet, Loader2, Upload, Truck,
  UploadCloud, X
} from "lucide-react"

interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: number
  unit_price: string
  subtotal: string
}

interface Prescription {
  status: string
  rejection_reason: string | null
}

interface Order {
  id: number
  order_code: string
  status: string
  payment_status: string
  payment_method: string
  grand_total: string
  created_at: string
  requires_prescription: boolean
  prescription: Prescription | null
  items: OrderItem[]
  payment_proof_url: string | null
  tracking_number: string | null
  payment_deadline: string | null
}

// Status map sesuai 7 status lifecycle baru
const STATUS_CONFIG: Record<string, { text: string; color: string; icon: any }> = {
  menunggu_verifikasi_resep: { 
    text: "Menunggu Verifikasi Resep", 
    color: "bg-amber-100 text-amber-700 border-amber-200",
    icon: FileText 
  },
  menunggu_pembayaran: { 
    text: "Menunggu Pembayaran", 
    color: "bg-orange-100 text-orange-700 border-orange-200",
    icon: Wallet 
  },
  menunggu_konfirmasi_kasir: { 
    text: "Menunggu Konfirmasi Kasir", 
    color: "bg-blue-100 text-blue-700 border-blue-200",
    icon: Clock 
  },
  diproses: { 
    text: "Diproses", 
    color: "bg-indigo-100 text-indigo-700 border-indigo-200",
    icon: Package 
  },
  dikirim: { 
    text: "Dikirim", 
    color: "bg-teal-100 text-teal-700 border-teal-200",
    icon: Truck 
  },
  selesai: { 
    text: "Selesai", 
    color: "bg-green-100 text-green-700 border-green-200",
    icon: CheckCircle 
  },
  dibatalkan: { 
    text: "Dibatalkan", 
    color: "bg-red-100 text-red-700 border-red-200",
    icon: XCircle 
  },
}

export default function OrderHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Upload bukti bayar state
  const [uploadingOrderId, setUploadingOrderId] = useState<number | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadPreview, setUploadPreview] = useState<string | null>(null)
  const [uploadModal, setUploadModal] = useState<number | null>(null)  // order_id
  const [uploadError, setUploadError] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Konfirmasi diterima state
  const [confirmingOrderId, setConfirmingOrderId] = useState<number | null>(null)

  useEffect(() => { fetchOrders() }, [])

  const fetchOrders = async () => {
    try {
      const res = await api.get("/orders")
      setOrders(res.data.items || [])
    } catch (err) {
      console.error("Failed to fetch orders", err)
    } finally {
      setIsLoading(false)
    }
  }

  const formatIDR = (price: string) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency", currency: "IDR", maximumFractionDigits: 0,
    }).format(parseFloat(price))
  }

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat("id-ID", {
      day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
    }).format(new Date(dateString))
  }

  const getStatusConfig = (status: string) => {
    return STATUS_CONFIG[status] ?? {
      text: status, color: "bg-slate-100 text-slate-700 border-slate-200", icon: Package
    }
  }

  // Handle upload bukti pembayaran
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith("image/")) {
      setUploadError("File harus berupa gambar (JPG, PNG, WebP).")
      return
    }
    setUploadFile(file)
    const reader = new FileReader()
    reader.onload = (ev) => setUploadPreview(ev.target?.result as string)
    reader.readAsDataURL(file)
    setUploadError("")
  }

  const handleUploadPaymentProof = async () => {
    if (!uploadModal || !uploadFile) return
    setUploadingOrderId(uploadModal)
    try {
      const formData = new FormData()
      formData.append("file", uploadFile)
      await api.post(`/orders/${uploadModal}/payment-proof`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })
      setUploadModal(null)
      setUploadFile(null)
      setUploadPreview(null)
      fetchOrders()
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || "Gagal mengupload bukti bayar.")
    } finally {
      setUploadingOrderId(null)
    }
  }

  // Handle konfirmasi pesanan diterima
  const handleConfirmReceived = async (orderId: number) => {
    if (!confirm("Konfirmasi bahwa pesanan sudah Anda terima?")) return
    setConfirmingOrderId(orderId)
    try {
      await api.post(`/orders/${orderId}/confirm-received`)
      fetchOrders()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal mengkonfirmasi pesanan.")
    } finally {
      setConfirmingOrderId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-[1400px]">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Pesanan Saya</h1>
        <p className="text-slate-500 mt-2">Pantau status pesanan dan riwayat belanja Anda.</p>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
            <Package className="w-10 h-10 text-slate-300" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">Belum Ada Pesanan</h3>
          <p className="text-slate-500 mt-2 mb-6">Anda belum pernah melakukan pemesanan.</p>
          <a href="/catalog" className="inline-flex items-center justify-center bg-teal-500 text-white rounded-xl px-6 py-3 font-medium hover:bg-teal-600 transition-colors">
            Mulai Belanja
          </a>
        </div>
      ) : (
        <div className="space-y-6">
          {orders.map((order) => {
            const statusConf = getStatusConfig(order.status)
            const StatusIcon = statusConf.icon

            return (
              <div key={order.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="bg-slate-50 border-b border-slate-100 px-6 py-4 flex flex-wrap gap-4 items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1 flex-wrap">
                      <Package className="w-5 h-5 text-slate-400 shrink-0" />
                      <span className="font-bold text-slate-900">Belanja • {formatDate(order.created_at)}</span>
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${statusConf.color}`}>
                        <StatusIcon className="w-3.5 h-3.5" />
                        {statusConf.text}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 pl-8">{order.order_code}</p>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Tombol Upload Bukti Transfer */}
                    {order.status === "menunggu_pembayaran" && (
                      <button
                        onClick={() => { setUploadModal(order.id); setUploadError(""); setUploadFile(null); setUploadPreview(null) }}
                        className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-colors"
                      >
                        <UploadCloud className="w-4 h-4" />
                        Upload Bukti Transfer
                      </button>
                    )}

                    {/* Tombol Konfirmasi Diterima */}
                    {order.status === "dikirim" && (
                      <button
                        onClick={() => handleConfirmReceived(order.id)}
                        disabled={confirmingOrderId === order.id}
                        className="flex items-center gap-2 bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-colors disabled:opacity-70"
                      >
                        {confirmingOrderId === order.id
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <CheckCircle className="w-4 h-4" />
                        }
                        Pesanan Diterima
                      </button>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  {/* Nomor resi */}
                  {order.tracking_number && (
                    <div className="mb-4 bg-teal-50 text-teal-700 p-3 rounded-xl border border-teal-200 text-sm flex gap-2 items-center">
                      <Truck className="w-4 h-4 shrink-0" />
                      <p><strong>No. Resi:</strong> {order.tracking_number}</p>
                    </div>
                  )}

                  {/* Penolakan resep */}
                  {order.requires_prescription && order.prescription?.status === "rejected" && (
                    <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-xl border border-red-200 text-sm flex gap-2">
                      <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                      <p><strong>Alasan Penolakan Resep:</strong> {order.prescription.rejection_reason}</p>
                    </div>
                  )}

                  <div className="flex flex-col md:flex-row justify-between gap-6">
                    <div className="flex-1">
                      {order.items.slice(0, 2).map((item, idx) => (
                        <div key={idx} className="flex gap-4 mb-4 last:mb-0">
                          <div className="w-16 h-16 bg-slate-50 rounded-lg border border-slate-100 flex-shrink-0 p-2">
                            <img src={`https://placehold.co/100x100/f8fafc/94a3b8?text=Obat`} alt={item.product_name} className="w-full h-full object-contain" />
                          </div>
                          <div>
                            <h4 className="font-bold text-slate-900 text-sm md:text-base line-clamp-1">{item.product_name}</h4>
                            <p className="text-slate-500 text-sm">{item.quantity} barang × {formatIDR(item.unit_price)}</p>
                          </div>
                        </div>
                      ))}
                      {order.items.length > 2 && (
                        <p className="text-sm text-teal-600 font-medium ml-20">+ {order.items.length - 2} produk lainnya</p>
                      )}
                    </div>

                    <div className="md:w-48 md:border-l md:border-slate-100 md:pl-6 flex flex-col justify-center">
                      <p className="text-sm text-slate-500 mb-1">Total Belanja</p>
                      <p className="text-lg font-bold text-slate-900 mb-3">{formatIDR(order.grand_total)}</p>
                      <button className="text-teal-600 font-bold text-sm flex items-center hover:text-teal-700 transition-colors">
                        Lihat Detail
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Upload Bukti Transfer Modal */}
      {uploadModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-800 text-lg">Upload Bukti Transfer</h3>
              <button
                onClick={() => setUploadModal(null)}
                className="text-slate-400 hover:text-slate-700 w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-slate-500 mb-4">
              Upload foto/screenshot bukti transfer Anda. Kasir akan memverifikasi pembayaran dalam 1×24 jam.
            </p>

            {uploadError && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-xl text-sm flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                {uploadError}
              </div>
            )}

            {!uploadFile ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:bg-slate-50 hover:border-teal-400 transition-colors mb-4"
              >
                <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-900">Klik untuk pilih gambar</p>
                <p className="text-xs text-slate-500 mt-1">JPG, PNG, WebP (Maks 5 MB)</p>
                <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept="image/*" className="hidden" />
              </div>
            ) : (
              <div className="relative border border-slate-200 rounded-xl overflow-hidden mb-4 group">
                <img src={uploadPreview!} alt="Preview" className="w-full h-48 object-cover" />
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button
                    type="button"
                    onClick={() => { setUploadFile(null); setUploadPreview(null) }}
                    className="bg-red-500 text-white p-2 rounded-full"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-2 text-xs text-slate-600 border-t">{uploadFile.name}</div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setUploadModal(null)}
                className="flex-1 border border-slate-200 text-slate-700 py-2.5 rounded-xl text-sm font-semibold hover:bg-slate-50"
              >
                Batal
              </button>
              <button
                onClick={handleUploadPaymentProof}
                disabled={!uploadFile || uploadingOrderId !== null}
                className="flex-1 bg-teal-500 hover:bg-teal-600 text-white py-2.5 rounded-xl text-sm font-bold transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {uploadingOrderId ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                Kirim Bukti
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from "react"
import { api } from "../../lib/api"
import { 
  Package, Clock, CheckCircle, XCircle, AlertTriangle, 
  ChevronRight, FileText, Download, Wallet, Loader2
} from "lucide-react"

interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: int
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
}

export default function OrderHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchOrders()
  }, [])

  const fetchOrders = async () => {
    try {
      // Assuming backend has GET /api/v1/orders that returns user's orders
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
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(parseFloat(price))
  }

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(dateString))
  }

  const getDisplayStatus = (order: Order) => {
    if (order.status === "cancelled") {
      return { text: "Dibatalkan", color: "bg-red-100 text-red-700 border-red-200", icon: XCircle }
    }
    
    if (order.requires_prescription) {
      if (!order.prescription) {
         return { text: "Menunggu Resep", color: "bg-amber-100 text-amber-700 border-amber-200", icon: AlertTriangle }
      }
      if (order.prescription.status === "pending") {
        return { text: "Menunggu Verifikasi Resep", color: "bg-amber-100 text-amber-700 border-amber-200", icon: FileText }
      }
      if (order.prescription.status === "rejected") {
        return { text: "Resep Ditolak", color: "bg-red-100 text-red-700 border-red-200", icon: XCircle }
      }
    }

    if (order.payment_status === "unpaid") {
      return { text: "Menunggu Pembayaran", color: "bg-orange-100 text-orange-700 border-orange-200", icon: Wallet }
    }

    if (["pending", "confirmed", "processing"].includes(order.status)) {
      return { text: "Diproses", color: "bg-blue-100 text-blue-700 border-blue-200", icon: Clock }
    }

    if (order.status === "ready") {
      return { text: "Siap Diambil", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: Package }
    }

    if (order.status === "completed") {
      return { text: "Selesai", color: "bg-green-100 text-green-700 border-green-200", icon: CheckCircle }
    }

    return { text: order.status, color: "bg-slate-100 text-slate-700 border-slate-200", icon: Package }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
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
          <a href="/catalog" className="inline-flex items-center justify-center bg-blue-600 text-white rounded-xl px-6 py-3 font-medium hover:bg-blue-700 transition-colors">
            Mulai Belanja
          </a>
        </div>
      ) : (
        <div className="space-y-6">
          {orders.map((order) => {
            const statusInfo = getDisplayStatus(order)
            const StatusIcon = statusInfo.icon
            
            return (
              <div key={order.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="bg-slate-50 border-b border-slate-100 px-6 py-4 flex flex-wrap gap-4 items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <Package className="w-5 h-5 text-slate-400" />
                      <span className="font-bold text-slate-900">Belanja • {formatDate(order.created_at)}</span>
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${statusInfo.color}`}>
                        <StatusIcon className="w-3.5 h-3.5" />
                        {statusInfo.text}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 pl-8">{order.order_code}</p>
                  </div>
                  
                  {statusInfo.text === "Menunggu Pembayaran" && (
                     <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-colors">
                       Cara Pembayaran
                     </button>
                  )}
                </div>

                {/* Content */}
                <div className="p-6">
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
                             {/* Placeholder image for item */}
                            <img src={`https://placehold.co/100x100/f8fafc/94a3b8?text=Obat`} alt={item.product_name} className="w-full h-full object-contain" />
                          </div>
                          <div>
                            <h4 className="font-bold text-slate-900 text-sm md:text-base line-clamp-1">{item.product_name}</h4>
                            <p className="text-slate-500 text-sm">{item.quantity} barang x {formatIDR(item.unit_price)}</p>
                          </div>
                        </div>
                      ))}
                      {order.items.length > 2 && (
                        <p className="text-sm text-blue-600 font-medium ml-20">+ {order.items.length - 2} produk lainnya</p>
                      )}
                    </div>
                    
                    <div className="md:w-48 md:border-l md:border-slate-100 md:pl-6 flex flex-col justify-center">
                      <p className="text-sm text-slate-500 mb-1">Total Belanja</p>
                      <p className="text-lg font-bold text-slate-900 mb-3">{formatIDR(order.grand_total)}</p>
                      
                      <button className="text-blue-600 font-bold text-sm flex items-center hover:text-blue-700 transition-colors">
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
    </div>
  )
}

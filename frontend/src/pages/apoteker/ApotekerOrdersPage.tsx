import { useEffect, useState, useCallback } from "react"
import { api } from "../../lib/api"
import {
  Loader2, RefreshCw, Clock, Search,
  ChevronLeft, ChevronRight, PackageCheck
} from "lucide-react"

interface OrderForApoteker {
  id: number
  order_code: string
  status: string
  customer_name: string
  customer_email: string
  grand_total: string
  payment_method: string
  tracking_number: string | null
  created_at: string
  items: { product_name: string; quantity: number; unit_price: string }[]
}

export default function ApotekerOrdersPage() {
  const [orders, setOrders] = useState<OrderForApoteker[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const PAGE_SIZE = 20

  const [searchInput, setSearchInput] = useState("")
  const [statusFilter, setStatusFilter] = useState("diproses")

  const [shipModal, setShipModal] = useState<{ orderId: number; orderCode: string } | null>(null)
  const [trackingNumber, setTrackingNumber] = useState("")
  const [processing, setProcessing] = useState<number | null>(null)

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      })
      if (statusFilter !== "all") params.set("status", statusFilter)
      if (searchInput) params.set("search", searchInput)

      const res = await api.get(`/orders?${params}`)
      const items = res.data.items || []
      setOrders(items)
      setHasMore(items.length === PAGE_SIZE)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, searchInput])

  useEffect(() => { fetchOrders() }, [fetchOrders])
  useEffect(() => { setPage(1) }, [statusFilter])

  const handleShip = async () => {
    if (!shipModal) return
    setProcessing(shipModal.orderId)
    try {
      await api.post(`/orders/${shipModal.orderId}/ship`, { tracking_number: trackingNumber.trim() })
      setShipModal(null)
      setTrackingNumber("")
      fetchOrders()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal mengirim pesanan")
    } finally {
      setProcessing(null)
    }
  }

  const formatIDR = (price: string) =>
    new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(parseFloat(price))

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })

  const STATUS_TABS = [
    { key: "diproses", label: "Perlu Dikirim" },
    { key: "dikirim", label: "Sedang Dikirim" },
    { key: "selesai", label: "Selesai" },
    { key: "all", label: "Semua" },
  ]

  const pendingCount = orders.filter(o => o.status === "diproses").length

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Pengiriman Pesanan</h1>
          <p className="text-slate-500 mt-1">Siapkan dan kirim pesanan pelanggan yang telah lunas.</p>
        </div>
        <div className="flex items-center gap-3">
          {pendingCount > 0 && statusFilter !== "diproses" && (
            <button
              onClick={() => setStatusFilter("diproses")}
              className="flex items-center gap-2 bg-indigo-50 border border-indigo-200 text-indigo-700 text-sm font-bold px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
              {pendingCount} perlu dikirim
            </button>
          )}
          <button
            onClick={fetchOrders}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-primary transition-colors px-3 py-2 rounded-lg hover:bg-slate-100"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex gap-2 flex-1 max-w-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Cari kode pesanan..."
              className="w-full pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchOrders()}
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1 bg-white border border-slate-200 rounded-xl p-1">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === tab.key
                  ? "bg-primary text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-6 animate-in fade-in duration-200">
            <div className="h-8 w-48 bg-slate-200 animate-pulse rounded mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4].map(i => <div key={i} className="h-40 bg-slate-100 animate-pulse rounded-xl"></div>)}
            </div>
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <PackageCheck className="w-14 h-14 mb-3 text-slate-300" />
            <p className="font-semibold text-slate-500 text-lg">Tidak ada pesanan</p>
            <p className="text-sm mt-1">Tidak ada pesanan yang sesuai dengan filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-5 py-3.5">Pesanan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Pelanggan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Total</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Resi Pengiriman</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Waktu Order</th>
                  <th className="text-center text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Status & Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono font-bold text-slate-800 text-xs bg-slate-100 px-2 py-1 rounded-md">
                        {order.order_code}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <p className="font-semibold text-slate-800">{order.customer_name}</p>
                      <p className="text-xs text-slate-400">{order.customer_email}</p>
                    </td>
                    <td className="px-4 py-4">
                      <span className="font-bold text-slate-900">{formatIDR(order.grand_total)}</span>
                    </td>
                    <td className="px-4 py-4">
                      {order.tracking_number ? (
                        <span className="font-mono text-xs text-indigo-700 bg-indigo-50 px-2 py-1 rounded">
                          {order.tracking_number}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1 text-slate-500 text-xs">
                        <Clock className="w-3.5 h-3.5 shrink-0" />
                        <span>{formatDate(order.created_at)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      {order.status === "diproses" ? (
                        <button
                          onClick={() => { setShipModal({ orderId: order.id, orderCode: order.order_code }); setTrackingNumber("") }}
                          disabled={processing === order.id}
                          className="inline-flex items-center gap-1 bg-primary hover:bg-primary/90 disabled:opacity-60 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                        >
                          {processing === order.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <PackageCheck className="w-3 h-3" />}
                          Kirim Pesanan
                        </button>
                      ) : (
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full inline-block ${
                          order.status === "dikirim" ? "bg-blue-100 text-blue-700" :
                          order.status === "selesai" ? "bg-emerald-100 text-emerald-700" :
                          "bg-slate-100 text-slate-600"
                        }`}>
                          {order.status.replace(/_/g, " ")}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && orders.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">Halaman {page} · {orders.length} data</p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center gap-1.5 px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Sebelumnya
            </button>
            <span className="px-3 py-2 text-sm font-semibold bg-primary/10 text-primary rounded-lg">{page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className="flex items-center gap-1.5 px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Berikutnya
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Ship Modal */}
      {shipModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="font-bold text-slate-800 text-lg mb-1">Kirim Pesanan</h3>
            <p className="text-sm text-slate-500 mb-4">
              Order <span className="font-mono font-bold text-slate-800">{shipModal.orderCode}</span>
            </p>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Nomor Resi (Opsional)
            </label>
            <input
              type="text"
              autoFocus
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              placeholder="JNE-123xxxx atau ambil di tempat..."
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
            />
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => { setShipModal(null); setTrackingNumber("") }}
                className="flex-1 border border-slate-200 text-slate-700 py-2.5 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleShip}
                disabled={processing !== null}
                className="flex-1 bg-primary hover:bg-primary/90 text-white py-2.5 rounded-xl text-sm font-bold transition-colors disabled:opacity-60"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Konfirmasi Kirim"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

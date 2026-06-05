import { useEffect, useState, useCallback } from "react"
import { api } from "../../lib/api"
import {
  CheckCircle, XCircle, Loader2, Eye, RefreshCw, Clock, Search,
  ChevronLeft, ChevronRight, Wallet, AlertTriangle
} from "lucide-react"

interface OrderForKasir {
  id: number
  order_code: string
  status: string
  customer_name: string
  customer_email: string
  grand_total: string
  payment_method: string
  payment_proof_url: string | null
  created_at: string
  items: { product_name: string; quantity: number; unit_price: string }[]
}

const API_BASE = import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000"

export default function KasirOrdersPage() {
  const [orders, setOrders] = useState<OrderForKasir[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const PAGE_SIZE = 20

  const [searchInput, setSearchInput] = useState("")
  const [statusFilter, setStatusFilter] = useState("menunggu_konfirmasi_kasir")

  const [imageModal, setImageModal] = useState<{ url: string; code: string } | null>(null)
  const [rejectModal, setRejectModal] = useState<{ orderId: number; orderCode: string } | null>(null)
  const [rejectReason, setRejectReason] = useState("")
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

  const handleConfirm = async (orderId: number) => {
    setProcessing(orderId)
    try {
      await api.post(`/orders/${orderId}/kasir/confirm`)
      fetchOrders()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal mengkonfirmasi pembayaran")
    } finally {
      setProcessing(null)
    }
  }

  const handleReject = async () => {
    if (!rejectModal) return
    if (!rejectReason.trim()) { alert("Alasan penolakan wajib diisi"); return }
    setProcessing(rejectModal.orderId)
    try {
      await api.post(`/orders/${rejectModal.orderId}/kasir/reject`, { reason: rejectReason.trim() })
      setRejectModal(null)
      setRejectReason("")
      fetchOrders()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal menolak pembayaran")
    } finally {
      setProcessing(null)
    }
  }

  const formatIDR = (price: string) =>
    new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(parseFloat(price))

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })

  const STATUS_TABS = [
    { key: "menunggu_konfirmasi_kasir", label: "Perlu Dikonfirmasi" },
    { key: "diproses", label: "Diproses" },
    { key: "all", label: "Semua" },
  ]

  const pendingCount = orders.filter(o => o.status === "menunggu_konfirmasi_kasir").length

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Konfirmasi Pembayaran</h1>
          <p className="text-slate-500 mt-1">Verifikasi bukti transfer dari pelanggan.</p>
        </div>
        <div className="flex items-center gap-3">
          {pendingCount > 0 && statusFilter !== "menunggu_konfirmasi_kasir" && (
            <button
              onClick={() => setStatusFilter("menunggu_konfirmasi_kasir")}
              className="flex items-center gap-2 bg-orange-50 border border-orange-200 text-orange-700 text-sm font-bold px-3 py-1.5 rounded-full hover:bg-orange-100 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
              {pendingCount} menunggu konfirmasi
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
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1">
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
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <Wallet className="w-14 h-14 mb-3 text-slate-300" />
            <p className="font-semibold text-slate-500 text-lg">Tidak ada pesanan</p>
            <p className="text-sm mt-1">Tidak ada pesanan yang perlu dikonfirmasi saat ini.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-5 py-3.5">Pesanan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Pelanggan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Total</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Metode</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Bukti Transfer</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Waktu</th>
                  <th className="text-center text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Aksi</th>
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
                      <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-full">
                        {order.payment_method}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      {order.payment_proof_url ? (
                        <button
                          onClick={() => setImageModal({ url: `${API_BASE}/static/${order.payment_proof_url}`, code: order.order_code })}
                          className="inline-flex items-center gap-1.5 text-primary hover:text-primary/80 text-xs font-semibold border border-primary/20 bg-primary/5 hover:bg-primary/10 px-2.5 py-1.5 rounded-lg transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Lihat Bukti
                        </button>
                      ) : (
                        <span className="text-slate-400 text-xs">Belum upload</span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1 text-slate-500 text-xs">
                        <Clock className="w-3.5 h-3.5 shrink-0" />
                        <span>{formatDate(order.created_at)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      {order.status === "menunggu_konfirmasi_kasir" ? (
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => handleConfirm(order.id)}
                            disabled={processing === order.id}
                            className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-xs font-bold px-2.5 py-1.5 rounded-lg transition-colors"
                          >
                            {processing === order.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                            Konfirmasi
                          </button>
                          <button
                            onClick={() => { setRejectModal({ orderId: order.id, orderCode: order.order_code }); setRejectReason("") }}
                            disabled={processing === order.id}
                            className="inline-flex items-center gap-1 bg-white hover:bg-red-50 disabled:opacity-60 text-red-600 border border-red-200 text-xs font-bold px-2.5 py-1.5 rounded-lg transition-colors"
                          >
                            <XCircle className="w-3 h-3" />
                            Tolak
                          </button>
                        </div>
                      ) : (
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                          order.status === "diproses" ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"
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

      {/* Reject Modal */}
      {rejectModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="font-bold text-slate-800 text-lg mb-1">Tolak Pembayaran</h3>
            <p className="text-sm text-slate-500 mb-4">
              Pesanan <span className="font-mono font-bold text-slate-800">{rejectModal.orderCode}</span>
            </p>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Alasan Penolakan <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={3}
              autoFocus
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
              placeholder="Contoh: Dana belum masuk rekening, bukti transfer palsu..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => { setRejectModal(null); setRejectReason("") }}
                className="flex-1 border border-slate-200 text-slate-700 py-2.5 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleReject}
                disabled={processing !== null}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-xl text-sm font-bold transition-colors disabled:opacity-60"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Tolak Pembayaran"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Modal */}
      {imageModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setImageModal(null)}>
          <div className="relative max-w-2xl w-full bg-white rounded-2xl overflow-hidden shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <div>
                <h3 className="font-bold text-slate-800">Bukti Transfer</h3>
                <p className="text-xs text-slate-500 mt-0.5">{imageModal.code}</p>
              </div>
              <button
                onClick={() => setImageModal(null)}
                className="text-slate-400 hover:text-slate-700 w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-4 flex items-center justify-center bg-slate-50 min-h-[300px]">
              <img
                src={imageModal.url}
                alt="Bukti Transfer"
                className="max-h-[65vh] object-contain rounded-lg shadow"
                onError={(e) => { (e.target as HTMLImageElement).src = "https://placehold.co/400x300/f8fafc/94a3b8?text=Gambar+tidak+tersedia" }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

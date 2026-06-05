import { useEffect, useState, useCallback } from "react"
import { api } from "../../lib/api"
import {
  ClipboardList, CheckCircle, XCircle, Loader2, Eye, RefreshCw, Clock,
  Search, ChevronLeft, ChevronRight, Filter
} from "lucide-react"

interface PrescriptionRecord {
  prescription_id: number
  order_id: number
  order_code: string
  customer_name: string
  drug_names: string
  image_url: string
  status: "pending" | "approved" | "rejected"
  rejection_reason: string | null
  pharmacist_name: string | null
  uploaded_at: string
  verified_at: string | null
}

const STATUS_CONFIG = {
  pending: {
    label: "Menunggu",
    badge: "bg-amber-100 text-amber-700 border border-amber-200",
    dot: "bg-amber-400",
  },
  approved: {
    label: "Disetujui",
    badge: "bg-emerald-100 text-emerald-700 border border-emerald-200",
    dot: "bg-emerald-400",
  },
  rejected: {
    label: "Ditolak",
    badge: "bg-red-100 text-red-700 border border-red-200",
    dot: "bg-red-400",
  },
} as const

export default function ApotekerVerifikasiPage() {
  const [records, setRecords] = useState<PrescriptionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [reviewing, setReviewing] = useState<number | null>(null)

  const [search, setSearch] = useState("")
  const [searchInput, setSearchInput] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const PAGE_SIZE = 20

  const [rejectModal, setRejectModal] = useState<{ orderId: number; orderCode: string } | null>(null)
  const [rejectReason, setRejectReason] = useState("")
  const [imageModal, setImageModal] = useState<{ url: string; code: string; name: string; status: string } | null>(null)

  const API_BASE = import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000"

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      })
      if (statusFilter !== "all") params.set("status", statusFilter)
      if (search) params.set("search", search)

      const res = await api.get(`/apoteker/prescriptions/history?${params}`)
      setRecords(res.data)
      setHasMore(res.data.length === PAGE_SIZE)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, search])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  // Reset to page 1 when filter/search changes
  useEffect(() => { setPage(1) }, [statusFilter, search])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(1)
  }

  const handleApprove = async (orderId: number) => {
    setReviewing(orderId)
    try {
      await api.patch(`/orders/${orderId}/prescription/review`, { action: "approved" })
      fetchHistory()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal menyetujui resep")
    } finally {
      setReviewing(null)
    }
  }

  const handleReject = async () => {
    if (!rejectModal) return
    if (!rejectReason.trim()) { alert("Alasan penolakan wajib diisi"); return }
    setReviewing(rejectModal.orderId)
    try {
      await api.patch(`/orders/${rejectModal.orderId}/prescription/review`, {
        action: "rejected",
        rejection_reason: rejectReason.trim(),
      })
      setRejectModal(null)
      setRejectReason("")
      fetchHistory()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal menolak resep")
    } finally {
      setReviewing(null)
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return "-"
    try {
      return new Date(iso).toLocaleString("id-ID", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit"
      })
    } catch { return iso }
  }

  const pendingCount = records.filter(r => r.status === "pending").length

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-500">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Riwayat Resep</h1>
          <p className="text-slate-500 mt-1">
            Semua riwayat verifikasi resep pasien beserta statusnya.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pendingCount > 0 && (
            <button
              onClick={() => { setStatusFilter("pending"); setPage(1) }}
              className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-700 text-sm font-bold px-3 py-1.5 rounded-full hover:bg-amber-100 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              {pendingCount} menunggu review
            </button>
          )}
          <button
            onClick={fetchHistory}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-primary transition-colors px-3 py-2 rounded-lg hover:bg-slate-100"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2 flex-1 max-w-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Cari kode pesanan / nama pasien..."
              className="w-full pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2.5 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-primary/90 transition-colors"
          >
            Cari
          </button>
        </form>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1">
          {(["all", "pending", "approved", "rejected"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === s
                  ? "bg-primary text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
              }`}
            >
              {s === "all" ? "Semua" :
               s === "pending" ? "Menunggu" :
               s === "approved" ? "Disetujui" : "Ditolak"}
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
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <ClipboardList className="w-14 h-14 mb-3 text-slate-300" />
            <p className="font-semibold text-slate-500 text-lg">Tidak ada data resep</p>
            <p className="text-sm mt-1">Coba ubah filter atau kata kunci pencarian.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-5 py-3.5">ID Pesanan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Pasien</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Obat Dipesan</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Status</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Apoteker</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Waktu Upload</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Foto</th>
                  <th className="text-center text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3.5">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((rx) => {
                  const statusConf = STATUS_CONFIG[rx.status] ?? STATUS_CONFIG.pending
                  return (
                    <tr key={rx.prescription_id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-mono font-bold text-slate-800 text-xs bg-slate-100 px-2 py-1 rounded-md">
                          {rx.order_code}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <p className="font-semibold text-slate-800">{rx.customer_name}</p>
                      </td>
                      <td className="px-4 py-4 max-w-[180px]">
                        <p className="text-slate-600 truncate text-xs" title={rx.drug_names}>
                          {rx.drug_names}
                        </p>
                      </td>
                      <td className="px-4 py-4">
                        <div>
                          <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${statusConf.badge}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${statusConf.dot}`} />
                            {statusConf.label}
                          </span>
                          {rx.status === "rejected" && rx.rejection_reason && (
                            <p className="text-xs text-red-500 mt-1 max-w-[150px] truncate" title={rx.rejection_reason}>
                              ↳ {rx.rejection_reason}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {rx.pharmacist_name ? (
                          <div>
                            <p className="text-slate-700 text-xs font-medium">{rx.pharmacist_name}</p>
                            {rx.verified_at && (
                              <p className="text-slate-400 text-xs mt-0.5">{formatDate(rx.verified_at)}</p>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 text-xs">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-1 text-slate-500 text-xs">
                          <Clock className="w-3.5 h-3.5 shrink-0" />
                          <span>{formatDate(rx.uploaded_at)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => setImageModal({
                            url: `${API_BASE}/${rx.image_url}`,
                            code: rx.order_code,
                            name: rx.customer_name,
                            status: rx.status,
                          })}
                          className="inline-flex items-center gap-1.5 text-primary hover:text-primary/80 text-xs font-semibold border border-primary/20 bg-primary/5 hover:bg-primary/10 px-2.5 py-1.5 rounded-lg transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Lihat
                        </button>
                      </td>
                      <td className="px-4 py-4">
                        {rx.status === "pending" ? (
                          <div className="flex items-center justify-center gap-1.5">
                            <button
                              onClick={() => handleApprove(rx.order_id)}
                              disabled={reviewing === rx.order_id}
                              className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-xs font-bold px-2.5 py-1.5 rounded-lg transition-colors"
                            >
                              {reviewing === rx.order_id
                                ? <Loader2 className="w-3 h-3 animate-spin" />
                                : <CheckCircle className="w-3 h-3" />}
                              Approve
                            </button>
                            <button
                              onClick={() => { setRejectModal({ orderId: rx.order_id, orderCode: rx.order_code }); setRejectReason("") }}
                              disabled={reviewing === rx.order_id}
                              className="inline-flex items-center gap-1 bg-white hover:bg-red-50 disabled:opacity-60 text-red-600 border border-red-200 text-xs font-bold px-2.5 py-1.5 rounded-lg transition-colors"
                            >
                              <XCircle className="w-3 h-3" />
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-xs text-center block">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && records.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Halaman {page} · {records.length} data
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center gap-1.5 px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Sebelumnya
            </button>
            <span className="px-3 py-2 text-sm font-semibold bg-primary/10 text-primary rounded-lg">
              {page}
            </span>
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
            <h3 className="font-bold text-slate-800 text-lg mb-1">Tolak Resep</h3>
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
              placeholder="Contoh: Resep tidak terbaca, stempel dokter tidak ada..."
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
                disabled={reviewing !== null}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-xl text-sm font-bold transition-colors disabled:opacity-60"
              >
                {reviewing ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Tolak Resep"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview Modal */}
      {imageModal && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setImageModal(null)}
        >
          <div
            className="relative max-w-2xl w-full bg-white rounded-2xl overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <div>
                <h3 className="font-bold text-slate-800">Foto Resep</h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-slate-500">{imageModal.code} — {imageModal.name}</p>
                  {imageModal.status && (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_CONFIG[imageModal.status as keyof typeof STATUS_CONFIG]?.badge}`}>
                      {STATUS_CONFIG[imageModal.status as keyof typeof STATUS_CONFIG]?.label}
                    </span>
                  )}
                </div>
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
                alt="Foto Resep"
                className="max-h-[65vh] object-contain rounded-lg shadow"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    "https://placehold.co/400x300/f8fafc/94a3b8?text=Gambar+tidak+tersedia"
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

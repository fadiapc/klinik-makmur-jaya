import { useEffect, useState, useCallback } from "react"
import { api } from "../../lib/api"
import {
  ClipboardList, Package, AlertTriangle, CheckCircle, XCircle,
  Loader2, Eye, RefreshCw, Clock
} from "lucide-react"

// ── Types ────────────────────────────────────────────────────────────────────

interface ApotekerStats {
  pending_prescriptions: number
  critical_stock_count: number
  near_expiry_count: number
}

interface PendingPrescription {
  order_id: number
  order_code: string
  customer_name: string
  drug_names: string
  image_url: string
  uploaded_at: string
}

interface NearExpiryItem {
  batch_id: number
  product_id: number
  product_name: string
  batch_number: string
  quantity_remaining: number
  expiry_date: string
  days_until_expiry: number
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ApotekerDashboardPage() {
  const [stats, setStats] = useState<ApotekerStats | null>(null)
  const [prescriptions, setPrescriptions] = useState<PendingPrescription[]>([])
  const [nearExpiry, setNearExpiry] = useState<NearExpiryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [reviewing, setReviewing] = useState<number | null>(null)
  const [rejectModal, setRejectModal] = useState<{ orderId: number; orderCode: string } | null>(null)
  const [rejectReason, setRejectReason] = useState("")
  const [imageModal, setImageModal] = useState<string | null>(null)

  const API_BASE = import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000"

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [statsRes, rxRes, expiryRes] = await Promise.all([
        api.get("/apoteker/stats"),
        api.get("/apoteker/prescriptions?limit=10"),
        api.get("/apoteker/near-expiry?limit=10"),
      ])
      setStats(statsRes.data)
      setPrescriptions(rxRes.data)
      setNearExpiry(expiryRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleApprove = async (orderId: number) => {
    setReviewing(orderId)
    try {
      await api.patch(`/orders/${orderId}/prescription/review`, { action: "approved" })
      setPrescriptions((prev) => prev.filter((p) => p.order_id !== orderId))
      setStats((s) => s ? { ...s, pending_prescriptions: Math.max(0, s.pending_prescriptions - 1) } : s)
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
      setPrescriptions((prev) => prev.filter((p) => p.order_id !== rejectModal.orderId))
      setStats((s) => s ? { ...s, pending_prescriptions: Math.max(0, s.pending_prescriptions - 1) } : s)
      setRejectModal(null)
      setRejectReason("")
    } catch (err: any) {
      alert(err.response?.data?.detail || "Gagal menolak resep")
    } finally {
      setReviewing(null)
    }
  }

  const getExpiryColor = (days: number) => {
    if (days <= 30) return "bg-red-50 border-red-200 text-red-700"
    if (days <= 60) return "bg-amber-50 border-amber-200 text-amber-700"
    return "bg-yellow-50 border-yellow-200 text-yellow-700"
  }

  const getExpiryBadge = (days: number) => {
    if (days <= 30) return "bg-red-100 text-red-700"
    if (days <= 60) return "bg-amber-100 text-amber-700"
    return "bg-yellow-100 text-yellow-700"
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" })
    } catch { return iso }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-500">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard Apoteker</h1>
          <p className="text-slate-500 mt-1">Ringkasan tugas verifikasi dan pemantauan stok farmasi (Sistem FIFO).</p>
        </div>
        <button
          onClick={fetchAll}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-primary transition-colors px-3 py-2 rounded-lg hover:bg-slate-100"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pending RX */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Antrian Resep Online</p>
              <p className="text-4xl font-black text-slate-800 mt-1">{stats?.pending_prescriptions ?? 0}</p>
              <p className="text-xs text-red-500 font-medium mt-2 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Menunggu Verifikasi
              </p>
            </div>
            <div className="bg-red-50 p-3 rounded-xl">
              <ClipboardList className="w-7 h-7 text-red-400" />
            </div>
          </div>
        </div>

        {/* Critical Stock */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Stok Obat Kritis</p>
              <p className="text-4xl font-black text-slate-800 mt-1">{stats?.critical_stock_count ?? 0}</p>
              <p className="text-xs text-amber-500 font-medium mt-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Di bawah ambang batas minimum
              </p>
            </div>
            <div className="bg-amber-50 p-3 rounded-xl">
              <Package className="w-7 h-7 text-amber-400" />
            </div>
          </div>
        </div>

        {/* Near Expiry */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Peringatan Kadaluarsa</p>
              <p className="text-4xl font-black text-slate-800 mt-1">{stats?.near_expiry_count ?? 0}</p>
              <p className="text-xs text-primary font-medium mt-2 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Expired dalam &lt; 90 hari
              </p>
            </div>
            <div className="bg-primary/10 p-3 rounded-xl">
              <AlertTriangle className="w-7 h-7 text-primary" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* Left: Prescription Queue */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="font-bold text-slate-800 text-lg">Antrian Verifikasi Resep</h2>
            <a href="/apoteker/verifikasi" className="text-sm font-medium text-primary hover:underline">
              Lihat Semua
            </a>
          </div>

          {prescriptions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <CheckCircle className="w-12 h-12 mb-3 text-green-300" />
              <p className="font-medium">Semua resep sudah diverifikasi!</p>
              <p className="text-sm mt-1">Tidak ada antrian yang menunggu.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-slate-50/50">
                    <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">ID Pesanan</th>
                    <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3">Pasien</th>
                    <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3">Dokumen Resep</th>
                    <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-4 py-3">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {prescriptions.map((rx) => (
                    <tr key={rx.order_id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-slate-800 text-xs">{rx.order_code}</td>
                      <td className="px-4 py-4">
                        <p className="font-semibold text-slate-800">{rx.customer_name}</p>
                        <p className="text-xs text-slate-500 truncate max-w-[120px]">{rx.drug_names}</p>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => setImageModal(`${API_BASE}/${rx.image_url}`)}
                          className="inline-flex items-center gap-1.5 text-primary hover:text-primary/80 text-xs font-semibold border border-primary/20 bg-primary/5 hover:bg-primary/10 px-3 py-1.5 rounded-lg transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Lihat Foto Resep
                        </button>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleApprove(rx.order_id)}
                            disabled={reviewing === rx.order_id}
                            className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            {reviewing === rx.order_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                            Approve
                          </button>
                          <button
                            onClick={() => { setRejectModal({ orderId: rx.order_id, orderCode: rx.order_code }); setRejectReason("") }}
                            disabled={reviewing === rx.order_id}
                            className="inline-flex items-center gap-1.5 bg-white hover:bg-red-50 disabled:opacity-60 text-red-600 border border-red-200 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <XCircle className="w-3 h-3" />
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Near Expiry FIFO Alert */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b">
            <div className="flex items-center gap-2 mb-0.5">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <h2 className="font-bold text-slate-800 text-base">Alert Kadaluarsa (FIFO)</h2>
            </div>
            <p className="text-xs text-slate-500">Mendekati Expired (&lt;= 90 Hari)</p>
          </div>

          <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
            {nearExpiry.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-slate-400">
                <CheckCircle className="w-10 h-10 mb-2 text-green-300" />
                <p className="text-sm font-medium">Tidak ada stok mendekati kadaluarsa</p>
              </div>
            ) : (
              nearExpiry.map((item) => (
                <div
                  key={item.batch_id}
                  className={`rounded-xl border p-4 ${getExpiryColor(item.days_until_expiry)}`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <p className="font-bold text-sm">{item.product_name}</p>
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${getExpiryBadge(item.days_until_expiry)}`}>
                      {item.days_until_expiry} HARI
                    </span>
                  </div>
                  <p className="text-xs opacity-80">
                    Batch: {item.batch_number} | Stok: {item.quantity_remaining}
                  </p>
                  <p className="text-xs font-medium mt-1 opacity-90">
                    Exp: {item.expiry_date}
                  </p>
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t">
            <a
              href="/apoteker/stok"
              className="block w-full text-center text-sm font-bold text-slate-700 border border-slate-200 hover:bg-slate-50 py-2.5 rounded-xl transition-colors"
            >
              Lihat Laporan FIFO Lengkap
            </a>
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {rejectModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="font-bold text-slate-800 text-lg mb-1">Tolak Resep</h3>
            <p className="text-sm text-slate-500 mb-4">Pesanan <span className="font-mono font-bold">{rejectModal.orderCode}</span></p>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Alasan Penolakan <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={3}
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
              placeholder="Contoh: Resep tidak terbaca, stempel dokter tidak ada, dll."
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
          <div className="relative max-w-2xl w-full bg-white rounded-2xl overflow-hidden shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h3 className="font-bold text-slate-800">Foto Resep</h3>
              <button onClick={() => setImageModal(null)} className="text-slate-400 hover:text-slate-700 text-xl">✕</button>
            </div>
            <div className="p-4 flex items-center justify-center bg-slate-50 min-h-[300px]">
              <img
                src={imageModal}
                alt="Foto Resep"
                className="max-h-[60vh] object-contain rounded-lg"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "https://placehold.co/400x300?text=Gambar+tidak+tersedia"
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

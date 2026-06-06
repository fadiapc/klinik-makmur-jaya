import { useState, useEffect } from "react"
import { PackagePlus, Search, Loader2 } from "lucide-react"
import { fetchStockBatches } from "../../services/apotekerService"
import type { StockBatchResponse } from "../../services/apotekerService"
import TambahBatchModal from "./components/TambahBatchModal"

export default function ApotekerBatchesPage() {
  const [batches, setBatches] = useState<StockBatchResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [search, setSearch] = useState("")
  const [isModalOpen, setIsModalOpen] = useState(false)

  const loadData = async (initial = false) => {
    if (initial) setIsLoading(true)
    else setIsSearching(true)
    
    try {
      const data = await fetchStockBatches(search)
      setBatches(data)
    } catch (error) {
      console.error(error)
    } finally {
      setIsLoading(false)
      setIsSearching(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadData(true)
  }, [])

  // Search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      loadData(false)
    }, 500)
    return () => clearTimeout(timer)
  }, [search])

  const formatRupiah = (value: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0
    }).format(value)
  }

  return (
    <div className="p-8 space-y-6 animate-in fade-in duration-200">
      
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Kelola Stok Batch</h1>
          <p className="text-muted-foreground mt-2">Daftar seluruh batch obat dan pengadaan barang baru dari supplier.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <PackagePlus className="w-4 h-4" />
          Terima Stok Baru
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        
        <div className="p-4 border-b bg-slate-50 flex items-center justify-between gap-4">
          <div className="relative w-full max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Cari nama produk atau nomor batch..."
              className="w-full pl-9 pr-10 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-2.5 h-4 w-4 text-primary animate-spin" />
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-12 bg-slate-50 animate-pulse rounded-lg w-full" />
              ))}
            </div>
          ) : batches.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-slate-500">
              Tidak ada data batch stok yang ditemukan.
            </div>
          ) : (
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="text-xs uppercase bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-4 font-semibold">Produk</th>
                  <th className="px-6 py-4 font-semibold">Nomor Batch</th>
                  <th className="px-6 py-4 font-semibold">Sisa Stok</th>
                  <th className="px-6 py-4 font-semibold">Harga Beli</th>
                  <th className="px-6 py-4 font-semibold">Kedaluwarsa</th>
                  <th className="px-6 py-4 font-semibold">Tgl Diterima</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {batches.map((batch) => {
                  const isExpired = batch.expiry_date && new Date(batch.expiry_date) < new Date()
                  const isNearExpiry = batch.expiry_date && !isExpired && (new Date(batch.expiry_date).getTime() - new Date().getTime()) / (1000 * 3600 * 24) <= 90

                  return (
                    <tr key={batch.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-900">{batch.product_name}</td>
                      <td className="px-6 py-4">{batch.batch_number}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          batch.quantity === 0 ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-blue-700'
                        }`}>
                          {batch.quantity}
                        </span>
                      </td>
                      <td className="px-6 py-4">{formatRupiah(batch.purchase_price)}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          isExpired ? 'bg-red-100 text-red-700' :
                          isNearExpiry ? 'bg-orange-100 text-orange-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {batch.expiry_date ? new Date(batch.expiry_date).toLocaleDateString('id-ID') : '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {new Date(batch.received_at).toLocaleDateString('id-ID')}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <TambahBatchModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={() => {
          setIsModalOpen(false)
          loadData()
        }}
      />
    </div>
  )
}

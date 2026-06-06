import { useState, useEffect } from "react"
import { X, Loader2, Search } from "lucide-react"
import { createStockBatch } from "../../../services/apotekerService"
import { getProducts } from "../../../services/productService"
import type { Product } from "../../../services/productService"

interface TambahBatchModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function TambahBatchModal({ isOpen, onClose, onSuccess }: TambahBatchModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [search, setSearch] = useState("")
  
  const [formData, setFormData] = useState({
    product_id: "",
    batch_number: "",
    quantity: "",
    purchase_price: "",
    expiry_date: ""
  })

  useEffect(() => {
    if (isOpen) {
      loadProducts()
      setFormData({
        product_id: "",
        batch_number: "",
        quantity: "",
        purchase_price: "",
        expiry_date: ""
      })
      setSearch("")
    }
  }, [isOpen])

  const loadProducts = async () => {
    try {
      const data = await getProducts({ limit: 1000 })
      setProducts(data.items || [])
    } catch (err) {
      console.error(err)
    }
  }

  if (!isOpen) return null

  const filteredProducts = products.filter(p => p.name.toLowerCase().includes(search.toLowerCase()))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await createStockBatch({
        product_id: Number(formData.product_id),
        batch_number: formData.batch_number,
        quantity: Number(formData.quantity),
        purchase_price: Number(formData.purchase_price),
        expiry_date: formData.expiry_date || null
      })
      onSuccess()
    } catch (err: any) {
      console.error(err)
      alert(err.response?.data?.detail || "Gagal menyimpan batch")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-bold text-slate-800">Terima Stok Baru (Batch)</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <form id="batchForm" onSubmit={handleSubmit} className="space-y-4">
            
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700">Pilih Produk <span className="text-red-500">*</span></label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Cari nama produk..."
                  className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="mt-2 max-h-40 overflow-y-auto border rounded-lg custom-scrollbar">
                {filteredProducts.length === 0 ? (
                  <p className="p-3 text-sm text-slate-500 text-center">Produk tidak ditemukan</p>
                ) : (
                  <div className="divide-y">
                    {filteredProducts.map(p => (
                      <div 
                        key={p.id}
                        onClick={() => setFormData({ ...formData, product_id: p.id.toString() })}
                        className={`p-3 text-sm cursor-pointer hover:bg-slate-50 flex justify-between items-center ${formData.product_id === p.id.toString() ? 'bg-primary/5 border-l-2 border-primary' : ''}`}
                      >
                        <span className="font-medium text-slate-800">{p.name}</span>
                        <span className="text-xs text-slate-500">{p.sku}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700">Nomor Batch <span className="text-red-500">*</span></label>
              <input
                type="text"
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                value={formData.batch_number}
                onChange={e => setFormData({ ...formData, batch_number: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700">Jumlah (Qty) <span className="text-red-500">*</span></label>
                <input
                  type="number"
                  required
                  min="1"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  value={formData.quantity}
                  onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700">Harga Beli (Satuan) <span className="text-red-500">*</span></label>
                <input
                  type="number"
                  required
                  min="0"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  value={formData.purchase_price}
                  onChange={e => setFormData({ ...formData, purchase_price: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700">Tanggal Kedaluwarsa (Opsional)</label>
              <input
                type="date"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                value={formData.expiry_date}
                onChange={e => setFormData({ ...formData, expiry_date: e.target.value })}
              />
            </div>

          </form>
        </div>

        <div className="p-4 border-t bg-slate-50 flex justify-end gap-3 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Batal
          </button>
          <button
            type="submit"
            form="batchForm"
            disabled={isSubmitting || !formData.product_id}
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            Simpan Batch
          </button>
        </div>

      </div>
    </div>
  )
}

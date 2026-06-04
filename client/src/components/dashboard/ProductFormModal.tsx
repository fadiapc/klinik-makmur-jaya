import React, { useState, useEffect } from "react"
import type { Product, ProductCreate } from "../../services/productService"
import { X, Loader2 } from "lucide-react"

interface ProductFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: ProductCreate, imageFile?: File) => Promise<void>
  initialData?: Product
}

export default function ProductFormModal({ isOpen, onClose, onSubmit, initialData }: ProductFormModalProps) {
  const [formData, setFormData] = useState<ProductCreate>({
    sku: "",
    name: "",
    category_id: 1, // Defaulting to 1 as requested for now
    supplier_id: 1,
    description: "",
    composition: "",
    dosage: "",
    side_effects: "",
    price: 0,
    requires_prescription: false,
    min_stock_threshold: 10
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [imageFile, setImageFile] = useState<File | undefined>(undefined)

  useEffect(() => {
    if (initialData) {
      setFormData({
        sku: initialData.sku,
        name: initialData.name,
        category_id: initialData.category.id,
        supplier_id: initialData.supplier.id,
        description: initialData.description || "",
        composition: initialData.composition || "",
        dosage: initialData.dosage || "",
        side_effects: initialData.side_effects || "",
        price: initialData.price,
        requires_prescription: initialData.requires_prescription,
        min_stock_threshold: initialData.min_stock_threshold
      })
    } else {
      setFormData({
        sku: "",
        name: "",
        category_id: 1,
        supplier_id: 1,
        description: "",
        composition: "",
        dosage: "",
        side_effects: "",
        price: 0,
        requires_prescription: false,
        min_stock_threshold: 10
      })
    }
    setError("")
    setImageFile(undefined)
  }, [initialData, isOpen])

  if (!isOpen) return null

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked
      setFormData(prev => ({ ...prev, [name]: checked }))
    } else if (type === "number") {
      setFormData(prev => ({ ...prev, [name]: Number(value) }))
    } else {
      setFormData(prev => ({ ...prev, [name]: value }))
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setImageFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError("")
    try {
      await onSubmit(formData, imageFile)
      onClose()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(", "))
      } else {
        setError(detail || "Gagal menyimpan produk. Periksa kembali data Anda.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">
            {initialData ? "Edit Produk" : "Tambah Produk Baru"}
          </h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-6 p-4 rounded-md bg-red-50 text-red-700 text-sm border border-red-100">
              {error}
            </div>
          )}

          <form id="product-form" onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">SKU <span className="text-red-500">*</span></label>
                <input 
                  type="text" name="sku" required value={formData.sku} onChange={handleChange}
                  disabled={!!initialData}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none disabled:bg-slate-100 disabled:text-slate-500" 
                  placeholder="Misal: OBT-001"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Nama Produk <span className="text-red-500">*</span></label>
                <input 
                  type="text" name="name" required value={formData.name} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                  placeholder="Mis. Panadol 500mg"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">ID Kategori (Semetara)</label>
                <input 
                  type="number" name="category_id" required min="1" value={formData.category_id} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">ID Supplier (Sementara)</label>
                <input 
                  type="number" name="supplier_id" required min="1" value={formData.supplier_id} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Harga (Rp) <span className="text-red-500">*</span></label>
                <input 
                  type="number" name="price" required min="0" value={formData.price} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Batas Stok Minimum</label>
                <input 
                  type="number" name="min_stock_threshold" required min="0" value={formData.min_stock_threshold} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Deskripsi</label>
              <textarea 
                name="description" value={formData.description} onChange={handleChange} rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none resize-none" 
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Komposisi</label>
              <textarea 
                name="composition" value={formData.composition} onChange={handleChange} rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none resize-none" 
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Dosis / Aturan Pakai</label>
                <input 
                  type="text" name="dosage" value={formData.dosage} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Efek Samping</label>
                <input 
                  type="text" name="side_effects" value={formData.side_effects} onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none" 
                />
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <input 
                type="checkbox" id="requires_prescription" name="requires_prescription" 
                checked={formData.requires_prescription} onChange={handleChange}
                className="w-4 h-4 text-primary rounded focus:ring-primary"
              />
              <label htmlFor="requires_prescription" className="text-sm font-medium text-slate-700 cursor-pointer">
                Wajib Resep Dokter (Obat Keras)
              </label>
            </div>

            <div className="space-y-2 border-t border-slate-100 pt-4">
              <label className="text-sm font-medium text-slate-700">Foto Produk (Opsional)</label>
              <input 
                type="file" accept="image/jpeg, image/png, image/webp" onChange={handleImageChange}
                className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 transition-colors"
              />
              <p className="text-xs text-slate-500">Maksimal 2MB. Format: JPG, PNG, WebP.</p>
            </div>
          </form>
        </div>

        <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
          <button 
            type="button" onClick={onClose} disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
          >
            Batal
          </button>
          <button 
            type="submit" form="product-form" disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {initialData ? "Simpan Perubahan" : "Tambah Produk"}
          </button>
        </div>

      </div>
    </div>
  )
}

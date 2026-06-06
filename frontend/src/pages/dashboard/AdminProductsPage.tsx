import React, { useState, useEffect, useCallback } from "react"
import { Plus, Search, Edit2, Trash2, UploadCloud, Loader2, LayoutGrid, List } from "lucide-react"
import { getProducts, deleteProduct, createProduct, updateProduct, uploadProductImage } from "../../services/productService"
import type { Product, ProductCreate } from "../../services/productService"
import ProductFormModal from "../../components/dashboard/ProductFormModal"
import BatchImportModal from "../../components/dashboard/BatchImportModal"

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState("")
  
  // Pagination
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  
  // Modals state
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | undefined>(undefined)
  
  // View mode
  const [viewMode, setViewMode] = useState<"table" | "grid">("table")

  const fetchProductsList = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await getProducts({ page, page_size: 20, q: search })
      setProducts(res.items || [])
      setTotalPages(res.total_pages || 1)
    } catch (error) {
      console.error("Failed to fetch products", error)
    } finally {
      setIsLoading(false)
    }
  }, [page, search])

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchProductsList()
    }, 500)
    return () => clearTimeout(delayDebounceFn)
  }, [fetchProductsList])

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const handleDelete = async (id: number, name: string) => {
    if (window.confirm(`Apakah Anda yakin ingin menghapus produk "${name}"?`)) {
      try {
        await deleteProduct(id)
        fetchProductsList()
      } catch (error) {
        console.error("Failed to delete product", error)
        alert("Gagal menghapus produk.")
      }
    }
  }

  const handleFormSubmit = async (data: ProductCreate, imageFile?: File) => {
    let productId: number

    if (editingProduct) {
      const res = await updateProduct(editingProduct.id, data)
      productId = res.id
    } else {
      const res = await createProduct(data)
      productId = res.id
    }

    if (imageFile && productId) {
      await uploadProductImage(productId, imageFile)
    }

    fetchProductsList()
  }

  const openEditModal = (product: Product) => {
    setEditingProduct(product)
    setIsFormModalOpen(true)
  }

  const openCreateModal = () => {
    setEditingProduct(undefined)
    setIsFormModalOpen(true)
  }

  return (
    <div className="p-8 space-y-6 animate-in fade-in duration-200">
      
      {/* Header Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Kelola Produk</h1>
          <p className="text-muted-foreground mt-1">Manajemen inventori obat dan alat kesehatan.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center gap-2 bg-white text-slate-700 border border-slate-300 px-4 py-2 rounded-md hover:bg-slate-50 transition-colors shadow-sm font-medium"
          >
            <UploadCloud className="w-4 h-4" />
            Import CSV
          </button>
          <button 
            onClick={openCreateModal}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors shadow-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Tambah Produk
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search className="h-4 w-4" />
            </div>
            <input 
              type="text" 
              placeholder="Cari berdasarkan nama atau SKU..." 
              value={search}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-shadow text-sm"
            />
          </div>
          
          <div className="flex bg-slate-100 p-1 rounded-md border border-slate-200 self-end sm:self-auto">
            <button 
              onClick={() => setViewMode("table")}
              className={`p-1.5 rounded flex items-center justify-center transition-colors ${viewMode === "table" ? "bg-white shadow-sm text-primary" : "text-slate-500 hover:text-slate-700"}`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded flex items-center justify-center transition-colors ${viewMode === "grid" ? "bg-white shadow-sm text-primary" : "text-slate-500 hover:text-slate-700"}`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Content Area */}
        <div className="flex-1 min-h-[400px] bg-white relative">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10 backdrop-blur-sm">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : products.length === 0 ? (
            <div className="p-12 flex flex-col items-center justify-center text-center h-full">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <Search className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-900">Tidak ada produk ditemukan</h3>
              <p className="text-slate-500 mt-1 max-w-sm">
                Coba sesuaikan kata kunci pencarian atau tambah produk baru.
              </p>
            </div>
          ) : viewMode === "table" ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-600">
                <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 font-semibold w-16">Gambar</th>
                    <th className="px-6 py-4 font-semibold">SKU</th>
                    <th className="px-6 py-4 font-semibold">Nama Produk</th>
                    <th className="px-6 py-4 font-semibold">Kategori</th>
                    <th className="px-6 py-4 font-semibold text-right">Harga</th>
                    <th className="px-6 py-4 font-semibold text-center">Resep</th>
                    <th className="px-6 py-4 font-semibold text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        {product.image_url ? (
                          <img src={`http://localhost:8000/static/${product.image_url}`} alt={product.name} className="w-10 h-10 object-cover rounded-md bg-white border border-slate-200" />
                        ) : (
                          <div className="w-10 h-10 rounded-md bg-slate-100 border border-slate-200 flex items-center justify-center text-lg">
                            💊
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-900">{product.sku}</td>
                      <td className="px-6 py-4">{product.name}</td>
                      <td className="px-6 py-4">
                        <span className="bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-full text-xs font-medium border border-slate-200">
                          {product.category?.name || "Tanpa Kategori"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right tabular-nums">
                        Rp {Number(product.price).toLocaleString('id-ID', { maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {product.requires_prescription ? (
                          <span className="text-amber-600 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                            Ya
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button 
                          onClick={() => openEditModal(product)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors" 
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDelete(product.id, product.name)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors" 
                          title="Hapus"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {products.map((product) => (
                <div key={product.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group flex flex-col">
                  <div className="relative aspect-square bg-slate-100 flex items-center justify-center p-4">
                    {product.image_url ? (
                      <img src={`http://localhost:8000/static/${product.image_url}`} alt={product.name} className="object-contain w-full h-full" />
                    ) : (
                      <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-sm text-2xl">
                        💊
                      </div>
                    )}
                    <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => openEditModal(product)} className="p-1.5 bg-white text-blue-600 shadow-sm rounded hover:bg-blue-50">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(product.id, product.name)} className="p-1.5 bg-white text-red-600 shadow-sm rounded hover:bg-red-50">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="p-4 flex flex-col flex-1">
                    <div className="text-xs font-medium text-slate-500 mb-1">{product.sku}</div>
                    <h3 className="font-semibold text-slate-900 line-clamp-2 mb-2 flex-1">{product.name}</h3>
                    
                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100">
                      <span className="font-bold text-primary">Rp {Number(product.price).toLocaleString('id-ID', { maximumFractionDigits: 0 })}</span>
                      {product.requires_prescription && (
                        <span className="text-[10px] uppercase font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          Resep
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-200 bg-white flex items-center justify-between">
            <p className="text-sm text-slate-600">
              Halaman <span className="font-medium text-slate-900">{page}</span> dari <span className="font-medium text-slate-900">{totalPages}</span>
            </p>
            <div className="flex gap-2">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700"
              >
                Sebelumnya
              </button>
              <button 
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700"
              >
                Selanjutnya
              </button>
            </div>
          </div>
        )}
      </div>

      <ProductFormModal 
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSubmit={handleFormSubmit}
        initialData={editingProduct}
      />

      <BatchImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          setIsImportModalOpen(false)
          fetchProductsList()
        }}
      />
    </div>
  )
}

import React, { useState, useEffect } from "react"
import { X, Loader2 } from "lucide-react"
import type { Role, User, UserCreateData, UserUpdateData } from "../../services/userService"

interface UserFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: UserCreateData | UserUpdateData) => Promise<void>
  initialData?: User | null
  roles: Role[]
}

export default function UserFormModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  roles,
}: UserFormModalProps) {
  const [formData, setFormData] = useState<UserCreateData>({
    name: "",
    email: "",
    role_id: roles.length > 0 ? roles[0].id : 1,
    phone: "",
    is_active: true,
  })
  
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Update form data when modal opens or initialData changes
  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData({
          name: initialData.name,
          email: initialData.email,
          role_id: initialData.role.id,
          phone: initialData.phone || "",
          is_active: initialData.is_active,
        })
      } else {
        setFormData({
          name: "",
          email: "",
          role_id: roles.length > 0 ? roles[0].id : 1,
          phone: "",
          is_active: true,
        })
      }
      setError(null)
    }
  }, [isOpen, initialData, roles])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked
      setFormData(prev => ({ ...prev, [name]: checked }))
    } else if (name === "role_id") {
      setFormData(prev => ({ ...prev, [name]: parseInt(value) }))
    } else {
      setFormData(prev => ({ ...prev, [name]: value }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await onSave(formData)
      onClose()
    } catch (err: any) {
      setError(err.message || "Terjadi kesalahan saat menyimpan data")
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-800">
            {initialData ? "Ubah Data Pengguna" : "Tambah Pengguna Baru"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Nama Lengkap <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                required
                minLength={2}
                maxLength={100}
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                placeholder="Masukkan nama lengkap"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Alamat Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                placeholder="nama@klinik.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Role (Peran) <span className="text-red-500">*</span>
              </label>
              <select
                name="role_id"
                required
                value={formData.role_id}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              >
                {roles.map(role => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Nomor Telepon
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                placeholder="08123456789"
              />
            </div>

            {!initialData && (
              <div className="p-3 bg-primary/10 text-primary rounded-lg text-sm border border-primary/20 flex gap-2">
                <span className="font-medium">Info:</span>
                <span>
                  Password default untuk akun baru adalah <strong>Klinik123!</strong>
                </span>
              </div>
            )}
          </div>

          <div className="mt-8 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors font-medium"
            >
              Batal
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Menyimpan...
                </>
              ) : (
                "Simpan"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

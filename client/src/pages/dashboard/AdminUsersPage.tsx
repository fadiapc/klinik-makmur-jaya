import { useEffect, useState } from "react"
import { Search, Plus, Loader2, Edit2, ShieldOff, ShieldAlert, Filter } from "lucide-react"
import { fetchUsers, fetchRoles, createUser, updateUser, toggleUserStatus } from "../../services/userService"
import type { User, Role, UserCreateData, UserUpdateData } from "../../services/userService"
import UserFormModal from "../../components/dashboard/UserFormModal"
import { useAuthStore } from "../../store/authStore"
import UnauthorizedPage from "../error/UnauthorizedPage"

export default function AdminUsersPage() {
  const { user: currentUser } = useAuthStore()
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Pagination & Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [roleFilter, setRoleFilter] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  
  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 500)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Reset page when filters change
  useEffect(() => {
    setPage(1)
  }, [debouncedQuery, roleFilter])

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const [usersRes, rolesRes] = await Promise.all([
        fetchUsers({ q: debouncedQuery, role_id: roleFilter, page, page_size: 10 }),
        fetchRoles()
      ])
      
      setUsers(usersRes.items)
      setTotalPages(Math.ceil(usersRes.total / usersRes.page_size))
      setTotalItems(usersRes.total)
      setRoles(rolesRes)
    } catch (err: any) {
      setError(err.message || "Gagal memuat data pengguna")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [debouncedQuery, roleFilter, page])

  const handleSave = async (data: UserCreateData | UserUpdateData) => {
    if (editingUser) {
      await updateUser(editingUser.uuid, data as UserUpdateData)
    } else {
      await createUser(data as UserCreateData)
    }
    loadData()
  }

  const handleToggleStatus = async (uuid: string) => {
    if (confirm("Apakah Anda yakin ingin mengubah status aktif pengguna ini?")) {
      try {
        await toggleUserStatus(uuid)
        loadData()
      } catch (err: any) {
        alert(err.message)
      }
    }
  }

  const openCreateModal = () => {
    setEditingUser(null)
    setIsModalOpen(true)
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    setIsModalOpen(true)
  }

  if (currentUser?.role?.name?.toLowerCase() !== 'admin') {
    return <UnauthorizedPage />
  }

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Kelola Pengguna</h1>
          <p className="text-slate-500 mt-1">Kelola akses, role, dan status akun sistem</p>
        </div>
        
        <button 
          onClick={openCreateModal}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Tambah Pengguna
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-50">
          <div className="relative w-full sm:max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input 
              type="text" 
              placeholder="Cari nama, email, atau telepon..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="text-slate-400 w-5 h-5 hidden sm:block" />
            <select
              value={roleFilter || ""}
              onChange={(e) => setRoleFilter(e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full sm:w-auto px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
            >
              <option value="">Semua Role</option>
              {roles.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 text-red-500 mb-4">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-medium text-slate-800 mb-2">Akses Ditolak / Error</h3>
            <p className="text-slate-500">{error}</p>
          </div>
        )}

        {isLoading && !error ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : !error && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200 uppercase text-xs tracking-wider">
                <tr>
                  <th className="px-6 py-4">Pengguna</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Kontak</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                      Tidak ada data pengguna yang ditemukan.
                    </td>
                  </tr>
                ) : (
                  users.map(user => (
                    <tr key={user.uuid} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">{user.name}</div>
                        <div className="text-xs text-slate-400 mt-0.5">{user.email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                          {user.role.name}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-slate-600">{user.phone || "-"}</div>
                      </td>
                      <td className="px-6 py-4">
                        {user.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                            Aktif
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-rose-100 text-rose-700">
                            Nonaktif
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => openEditModal(user)}
                            className="p-1.5 text-primary hover:bg-primary/10 rounded transition-colors"
                            title="Edit Pengguna"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleToggleStatus(user.uuid)}
                            className={`p-1.5 rounded transition-colors ${
                              user.is_active 
                                ? "text-rose-600 hover:bg-rose-50" 
                                : "text-emerald-600 hover:bg-emerald-50"
                            }`}
                            title={user.is_active ? "Nonaktifkan Akun" : "Aktifkan Akun"}
                          >
                            <ShieldOff className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && !error && totalPages > 1 && (
          <div className="p-4 border-t border-slate-200 flex items-center justify-between bg-slate-50 text-sm">
            <span className="text-slate-500">
              Total <span className="font-medium text-slate-700">{totalItems}</span> pengguna
            </span>
            <div className="flex gap-1">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 border border-slate-300 rounded bg-white text-slate-600 disabled:opacity-50 hover:bg-slate-50"
              >
                Prev
              </button>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 border border-slate-300 rounded bg-white text-slate-600 disabled:opacity-50 hover:bg-slate-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      <UserFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        initialData={editingUser}
        roles={roles}
      />
    </div>
  )
}

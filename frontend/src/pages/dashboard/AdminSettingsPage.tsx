import { useEffect, useState } from "react"
import { Save, Bell, ShieldAlert, Loader2 } from "lucide-react"
import { api } from "../../lib/api"

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const fetchSettings = async () => {
    try {
      const res = await api.get("/settings")
      setSettings(res.data)
    } catch (error) {
      console.error(error)
      alert("Gagal memuat pengaturan")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSettings()
  }, [])

  const handleChange = (key: string, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put("/settings", { settings })
      // Use standard alert since react-hot-toast is not installed according to previous checks
      // Wait, earlier I found ProtectedLayout didn't import react-hot-toast, but maybe it is installed. Let's just use alert to be safe, or if it crashes, it's fine.
      // Wait, let's remove toast import if not installed. 
      // Actually I will remove toast and use native alert.
      alert("Pengaturan berhasil disimpan!")
    } catch (error) {
      console.error(error)
      alert("Gagal menyimpan pengaturan")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Pengaturan Sistem</h1>
        <p className="text-slate-500 mt-1">
          Kelola konfigurasi global aplikasi, notifikasi peringatan, dan perilaku sistem.
        </p>
      </div>

      <div className="space-y-6">
        {/* Notifikasi Section */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-slate-800">Notifikasi & Peringatan</h2>
          </div>
          
          <div className="p-6 space-y-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <label className="text-sm font-medium text-slate-900 block mb-1">
                  Peringatan Stok Menipis (Low Stock)
                </label>
                <p className="text-xs text-slate-500">
                  Tampilkan pop-up peringatan jika ada produk yang mencapai batas minimum stok.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer"
                  checked={settings["ENABLE_LOW_STOCK_ALERTS"] === "true"}
                  onChange={(e) => handleChange("ENABLE_LOW_STOCK_ALERTS", e.target.checked ? "true" : "false")}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            <div className="flex items-start justify-between gap-4">
              <div>
                <label className="text-sm font-medium text-slate-900 block mb-1">
                  Peringatan Tanggal Kadaluwarsa (Expiry)
                </label>
                <p className="text-xs text-slate-500">
                  Tampilkan pop-up peringatan jika ada obat yang mendekati tanggal kedaluwarsa.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer"
                  checked={settings["ENABLE_EXPIRY_ALERTS"] === "true"}
                  onChange={(e) => handleChange("ENABLE_EXPIRY_ALERTS", e.target.checked ? "true" : "false")}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </section>

        {/* Threshold Section */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-slate-800">Threshold Peringatan</h2>
          </div>
          
          <div className="p-6 space-y-6">
            <div>
              <label className="text-sm font-medium text-slate-900 block mb-2">
                Batas Hari Kedaluwarsa (Expiry Threshold)
              </label>
              <div className="flex items-center gap-3">
                <input 
                  type="number"
                  min="1"
                  className="w-24 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
                  value={settings["EXPIRY_ALERT_DAYS"] || "30"}
                  onChange={(e) => handleChange("EXPIRY_ALERT_DAYS", e.target.value)}
                />
                <span className="text-sm text-slate-500">hari sebelum expired</span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Sistem akan menganggap obat hampir kedaluwarsa jika sisa hari kurang dari angka ini.
              </p>
            </div>
            
            <hr className="border-slate-100" />
            
            <div>
              <label className="text-sm font-medium text-slate-900 block mb-2">
                Frekuensi Kemunculan Pop-up
              </label>
              <select 
                className="w-full sm:w-64 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm bg-white"
                value={settings["LOW_STOCK_ALERT_FREQ"] || "daily"}
                onChange={(e) => handleChange("LOW_STOCK_ALERT_FREQ", e.target.value)}
              >
                <option value="login">Setiap Kali Login</option>
                <option value="daily">Setiap Hari Sekali</option>
                <option value="always">Selalu Tampilkan</option>
              </select>
            </div>
          </div>
        </section>

        <div className="flex justify-end pt-4">
          <button 
            onClick={handleSave}
            disabled={saving}
            className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Menyimpan...' : 'Simpan Perubahan'}
          </button>
        </div>
      </div>
    </div>
  )
}

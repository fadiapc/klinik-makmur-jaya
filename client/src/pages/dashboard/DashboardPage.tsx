import { useAuthStore } from "../../store/authStore"
import { Users, Package, ShoppingCart, Activity } from "lucide-react"

export default function DashboardPage() {
  const { user } = useAuthStore()

  // Dummy statistics
  const stats = [
    {
      title: "Total Produk",
      value: "1,234",
      icon: <Package className="w-6 h-6 text-primary" />,
      description: "+12% dari bulan lalu"
    },
    {
      title: "Pesanan Aktif",
      value: "45",
      icon: <ShoppingCart className="w-6 h-6 text-primary" />,
      description: "Menunggu diproses"
    },
    {
      title: "Total Pasien",
      value: "892",
      icon: <Users className="w-6 h-6 text-primary" />,
      description: "+5% pasien baru"
    },
    {
      title: "Kesehatan Sistem",
      value: "99.9%",
      icon: <Activity className="w-6 h-6 text-primary" />,
      description: "Normal"
    }
  ]

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Selamat datang kembali, <span className="font-medium text-slate-900">{user?.name}</span>! Berikut ringkasan sistem hari ini.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="p-6 bg-white border border-slate-100 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{stat.value}</p>
              </div>
              <div className="p-3 bg-primary/10 rounded-lg">
                {stat.icon}
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-4">{stat.description}</p>
          </div>
        ))}
      </div>
      
      {/* Placeholder for future charts or tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="p-6 bg-white border border-slate-100 rounded-xl shadow-sm h-80 flex items-center justify-center">
          <p className="text-slate-400">Grafik Penjualan (Segera Hadir)</p>
        </div>
        <div className="p-6 bg-white border border-slate-100 rounded-xl shadow-sm h-80 flex items-center justify-center">
          <p className="text-slate-400">Pesanan Terbaru (Segera Hadir)</p>
        </div>
      </div>
    </div>
  )
}

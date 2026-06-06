import { useAuthStore } from "../../store/authStore"
import { useState, useEffect } from "react"
import { Users, Package, ShoppingCart, Activity, FileText, Loader2 } from "lucide-react"
import { api } from "../../lib/api"
import { fetchDashboardStats } from "../../services/dashboardService"
import type { DashboardStatsResponse } from "../../services/dashboardService"
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts"

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [isGenerating, setIsGenerating] = useState(false)
  
  const [statsData, setStatsData] = useState<DashboardStatsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await fetchDashboardStats()
        setStatsData(data)
      } catch (err) {
        console.error("Gagal mengambil data dashboard", err)
      } finally {
        setIsLoading(false)
      }
    }
    loadStats()
  }, [])

  const handleGenerateReport = async () => {
    setIsGenerating(true)
    try {
      await api.get(`/dashboard/reports/sales?format=pdf`)
    } catch (err) {
      console.error(err)
      alert("Gagal memulai pembuatan laporan")
    } finally {
      setTimeout(() => setIsGenerating(false), 1000)
    }
  }

  // Fallback / Loading state
  const stats = [
    {
      title: "Total Produk",
      value: statsData ? statsData.total_products.toLocaleString('id-ID') : "-",
      icon: <Package className="w-6 h-6 text-primary" />,
      description: "Produk aktif di katalog"
    },
    {
      title: "Pesanan Aktif",
      value: statsData ? statsData.active_orders.toLocaleString('id-ID') : "-",
      icon: <ShoppingCart className="w-6 h-6 text-primary" />,
      description: "Menunggu diproses/dikirim"
    },
    {
      title: "Total Pasien",
      value: statsData ? statsData.total_patients.toLocaleString('id-ID') : "-",
      icon: <Users className="w-6 h-6 text-primary" />,
      description: "Akun pasien terdaftar"
    },
    {
      title: "Kesehatan Sistem",
      value: statsData ? statsData.system_health : "-",
      icon: <Activity className="w-6 h-6 text-primary" />,
      description: "Normal"
    }
  ]

  const formatRupiah = (value: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-200">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Selamat datang kembali, <span className="font-medium text-slate-900">{user?.name}</span>! Berikut ringkasan sistem hari ini.
          </p>
        </div>
        
        <button 
          onClick={handleGenerateReport}
          disabled={isGenerating}
          className="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed whitespace-nowrap shadow-sm"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Memproses...
            </>
          ) : (
            <>
              <FileText className="w-4 h-4" /> Generate Laporan PDF
            </>
          )}
        </button>
      </div>

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
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            
            {/* Pesanan Terbaru */}
            <div className="p-6 bg-white border border-slate-100 rounded-xl shadow-sm flex flex-col h-96">
              <h2 className="text-lg font-bold text-slate-800 mb-4">Pesanan Terbaru</h2>
              <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {statsData?.recent_orders && statsData.recent_orders.length > 0 ? (
                  <div className="space-y-4">
                    {statsData.recent_orders.map((order: any) => (
                      <div key={order.id} className="p-4 border border-slate-100 rounded-lg flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-slate-800 text-sm">{order.order_code}</p>
                          <p className="text-xs text-slate-500">{order.customer_name} • {new Date(order.created_at).toLocaleDateString("id-ID")}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-slate-800 text-sm">{formatRupiah(order.grand_total)}</p>
                          <span className={`inline-block px-2 py-1 mt-1 text-[10px] font-semibold rounded-full ${
                            order.status === 'selesai' ? 'bg-green-100 text-green-700' :
                            order.status === 'dibatalkan' ? 'bg-red-100 text-red-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {order.status.replace(/_/g, ' ').toUpperCase()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-slate-400">Belum ada pesanan</p>
                  </div>
                )}
              </div>
            </div>

            {/* Grafik Penjualan */}
            <div className="p-6 bg-white border border-slate-100 rounded-xl shadow-sm flex flex-col h-96">
              <h2 className="text-lg font-bold text-slate-800 mb-4">Grafik Penjualan (30 Hari)</h2>
              <div className="flex-1 w-full h-full">
                {statsData?.sales_chart && statsData.sales_chart.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={statsData.sales_chart} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={(value) => {
                          const date = new Date(value);
                          return `${date.getDate()}/${date.getMonth() + 1}`;
                        }}
                        tick={{ fontSize: 12, fill: '#64748b' }}
                        tickLine={false}
                        axisLine={false}
                        minTickGap={20}
                      />
                      <YAxis 
                        width={65}
                        tickFormatter={(value) => {
                          if (value >= 1000000) return `Rp${(value / 1000000).toFixed(1)}Jt`;
                          if (value >= 1000) return `Rp${(value / 1000).toFixed(0)}rb`;
                          return `Rp${value}`;
                        }}
                        tick={{ fontSize: 12, fill: '#64748b' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip 
                        formatter={(value: any) => [formatRupiah(value || 0), "Total Penjualan"]}
                        labelFormatter={(label) => new Date(label).toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="total_sales" 
                        stroke="#0d9488" 
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6, fill: "#0d9488", stroke: "#fff", strokeWidth: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-slate-400">Belum ada data penjualan</p>
                  </div>
                )}
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  )
}

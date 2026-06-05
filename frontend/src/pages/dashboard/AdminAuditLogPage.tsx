import { useEffect, useState } from "react"
import { Search, Loader2, ShieldAlert } from "lucide-react"
import { 
  fetchAuditStats, 
  fetchAuditLogs
} from "../../services/auditService"
import type { DashboardStatsOut, AuditLogOut } from "../../services/auditService"
import { 
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar
} from "recharts"

export default function AdminAuditLogPage() {
  const [stats, setStats] = useState<DashboardStatsOut | null>(null)
  const [logs, setLogs] = useState<AuditLogOut[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [limit, setLimit] = useState(5)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [statsData, logsData] = await Promise.all([
        fetchAuditStats(),
        fetchAuditLogs(searchQuery, limit)
      ])
      setStats(statsData)
      setLogs(logsData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Initial load & search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      loadData()
    }, 500)
    return () => clearTimeout(timer)
  }, [searchQuery, limit])

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto text-center py-12 bg-white rounded-xl shadow-sm border border-slate-100">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="w-6 h-6 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">Akses Ditolak / Error</h2>
          <p className="text-slate-600">{error}</p>
        </div>
      </div>
    )
  }

  if (isLoading && !stats) {
    return (
      <div className="p-8 flex justify-center items-center h-[60vh]">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    )
  }

  if (!stats) return null

  // Format data for Donut chart
  const pieData = [
    { name: "Successful Logins", value: stats.auth_stats.successful_logins, color: "#009688" },
    { name: "Failed Logins", value: stats.auth_stats.failed_logins, color: "#dc2626" }
  ]

  // Format data for Bar chart
  const barData = [
    { name: "Authorized (All)", value: stats.authorization_stats.authorized_all },
    { name: "Role-Based (RBAC)", value: stats.authorization_stats.rbac },
    { name: "Object-Based (OBAC)", value: stats.authorization_stats.obac }
  ]

  // Current date for header
  const today = new Date().toLocaleDateString("id-ID", { 
    weekday: "long", day: "numeric", month: "long", year: "numeric" 
  })

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-end mb-6">
        <h1 className="text-2xl font-bold text-primary">Audit Keamanan</h1>
        <p className="text-primary font-medium">{today}</p>
      </div>

      {/* SECTION 1: Authentication */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-primary px-4 py-3">
          <h2 className="text-white font-medium">Authentication (Today)</h2>
        </div>
        
        <div className="p-6">
          {/* Top 3 Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="border border-slate-100 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm">
              <span className="text-slate-500 text-sm mb-2">Total Logins Today</span>
              <span className="text-4xl font-bold text-slate-800">{stats.auth_stats.total_logins_today}</span>
            </div>
            <div className="border border-slate-100 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm">
              <span className="text-slate-500 text-sm mb-2">Successful Logins</span>
              <span className="text-4xl font-bold text-primary">{stats.auth_stats.successful_logins}</span>
            </div>
            <div className="border border-slate-100 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm">
              <span className="text-slate-500 text-sm mb-2">Failed Logins</span>
              <span className="text-4xl font-bold text-red-600">{stats.auth_stats.failed_logins}</span>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="border border-slate-100 rounded-lg p-4">
              <h3 className="text-sm font-medium text-slate-700 mb-4">Login Success vs Failed</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend verticalAlign="bottom" height={36}/>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="border border-slate-100 rounded-lg p-4">
              <h3 className="text-sm font-medium text-slate-700 mb-4">Login Activity (Hourly)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={stats.hourly_activity}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="hour" tick={{fontSize: 12}} />
                    <YAxis tick={{fontSize: 12}} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="success" stroke="#009688" name="Success" strokeWidth={2} dot={{r: 4}} activeDot={{r: 6}} />
                    <Line type="monotone" dataKey="failed" stroke="#dc2626" name="Failed" strokeWidth={2} dot={{r: 4}} activeDot={{r: 6}} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: Authorization */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-primary px-4 py-3">
          <h2 className="text-white font-medium">Authorization (Access Controls)</h2>
        </div>
        <div className="p-6">
          <div className="h-64 border border-slate-100 rounded-lg p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={120} tick={{fontSize: 11}} />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#009688" barSize={30} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION 3: Accounting */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-primary px-4 py-3">
          <h2 className="text-white font-medium">Accounting (Audit Logs - Today)</h2>
        </div>
        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-lg font-medium text-slate-800">Recent Activity</h3>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6">
            <div className="relative w-full sm:w-96">
              <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Cari email, aktivitas, atau IP..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Tampilkan:</span>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-primary"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-100 text-slate-800 font-medium border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Activity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {logs.length > 0 ? (
                  logs.map((log) => {
                    const time = new Date(log.created_at).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
                    return (
                      <tr key={log.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-slate-600">{time}</td>
                        <td className="px-4 py-3 text-slate-800">{log.email}</td>
                        <td className="px-4 py-3 text-slate-600">{log.role_name}</td>
                        <td className="px-4 py-3 text-slate-800">{log.action}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            log.status === "Success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                          }`}>
                            {log.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{log.ip_address}</td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                      {isLoading ? "Memuat data..." : "Tidak ada log aktivitas ditemukan."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="mt-4 text-sm text-slate-500">
            Menampilkan {logs.length} aktivitas
          </div>
        </div>
      </div>
    </div>
  )
}

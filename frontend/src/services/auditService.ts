import { api } from "../lib/api"

export interface AuthStats {
  total_logins_today: number
  successful_logins: number
  failed_logins: number
}

export interface HourlyActivity {
  hour: string
  success: number
  failed: number
}

export interface AuthorizationStats {
  authorized_all: number
  rbac: number
  obac: number
}

export interface DashboardStatsOut {
  auth_stats: AuthStats
  hourly_activity: HourlyActivity[]
  authorization_stats: AuthorizationStats
}

export interface AuditLogOut {
  id: number
  created_at: string
  email: string
  role_name: string
  action: string
  module: string
  ip_address: string
  status: string
}

const ENDPOINT = "/audit"

export async function fetchAuditStats(): Promise<DashboardStatsOut> {
  try {
    const response = await api.get<DashboardStatsOut>(`${ENDPOINT}/stats`)
    return response.data
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Forbidden: Admin access required")
    }
    throw new Error(error.response?.data?.detail || "Failed to fetch audit stats")
  }
}

export async function fetchAuditLogs(q?: string, limit: number = 50): Promise<AuditLogOut[]> {
  try {
    const params: any = { limit }
    if (q) params.q = q
    
    const response = await api.get<AuditLogOut[]>(`${ENDPOINT}/logs`, { params })
    return response.data
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Forbidden: Admin access required")
    }
    throw new Error(error.response?.data?.detail || "Failed to fetch audit logs")
  }
}

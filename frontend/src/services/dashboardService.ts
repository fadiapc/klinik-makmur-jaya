import { api } from "../lib/api"
// import { OrderOut } from "./orderService"

export interface DailySales {
  date: string
  total_sales: number
}

export interface DashboardStatsResponse {
  total_products: number
  active_orders: number
  total_patients: number
  system_health: string
  recent_orders: any[] // Will replace with proper type if available
  sales_chart: DailySales[]
}

const ENDPOINT = "/dashboard"

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  const response = await api.get<DashboardStatsResponse>(`${ENDPOINT}/stats`)
  return response.data
}

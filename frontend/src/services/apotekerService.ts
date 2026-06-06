import { api } from "../lib/api"

export interface StockBatchResponse {
  id: number
  product_id: number
  product_name: string
  batch_number: string
  quantity: number
  purchase_price: number
  expiry_date: string | null
  received_at: string
}

export interface StockBatchCreate {
  product_id: number
  batch_number: string
  quantity: number
  purchase_price: number
  expiry_date: string | null
}

export const fetchStockBatches = async (search?: string): Promise<StockBatchResponse[]> => {
  const params = new URLSearchParams()
  if (search) params.append("search", search)
  
  const response = await api.get(`/apoteker/batches?${params.toString()}`)
  return response.data
}

export const createStockBatch = async (data: StockBatchCreate): Promise<StockBatchResponse> => {
  const response = await api.post('/apoteker/batches', data)
  return response.data
}

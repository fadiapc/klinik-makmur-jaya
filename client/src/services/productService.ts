import { api } from "../lib/api"

export interface Category {
  id: number
  name: string
}

export interface Supplier {
  id: number
  name: string
}

export interface Product {
  id: number
  sku: string
  name: string
  category: Category
  supplier: Supplier
  description: string | null
  composition: string | null
  dosage: string | null
  side_effects: string | null
  price: number
  requires_prescription: boolean
  min_stock_threshold: number
  image_url: string | null
  is_active: boolean
}

export interface ProductCreate {
  sku: string
  name: string
  category_id: number
  supplier_id: number
  description?: string
  composition?: string
  dosage?: string
  side_effects?: string
  price: number
  requires_prescription: boolean
  min_stock_threshold: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const getProducts = async (params?: any) => {
  const response = await api.get<PaginatedResponse<Product>>("/products", { params })
  return response.data
}

export const createProduct = async (data: ProductCreate) => {
  const response = await api.post<Product>("/products", data)
  return response.data
}

export const updateProduct = async (id: number, data: Partial<ProductCreate>) => {
  const payload = { ...data }
  // Backend forbids updating SKU, so we must strip it out
  if ('sku' in payload) {
    delete payload.sku
  }
  const response = await api.put<Product>(`/products/${id}`, payload)
  return response.data
}

export const deleteProduct = async (id: number) => {
  const response = await api.delete(`/products/${id}`)
  return response.data
}

export const uploadBatchCsv = async (file: File) => {
  const formData = new FormData()
  formData.append("file", file)
  let authHeader = ""
  try {
    const authState = JSON.parse(localStorage.getItem("auth-storage") || "{}")
    if (authState.state && authState.state.token) {
      authHeader = `Bearer ${authState.state.token}`
    }
  } catch (e) {}
  
  const response = await fetch("http://localhost:8000/api/v1/products/batch-import", {
    method: "POST",
    headers: authHeader ? { "Authorization": authHeader } : {},
    body: formData,
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw { response: { data: errorData } }
  }
  return response.json()
}

export const checkImportStatus = async (jobId: string) => {
  const response = await api.get(`/products/import-status/${jobId}`)
  return response.data
}

export const uploadProductImage = async (productId: number, file: File) => {
  const formData = new FormData()
  formData.append("file", file)
  let authHeader = ""
  try {
    const authState = JSON.parse(localStorage.getItem("auth-storage") || "{}")
    if (authState.state && authState.state.token) {
      authHeader = `Bearer ${authState.state.token}`
    }
  } catch (e) {}

  const response = await fetch(`http://localhost:8000/api/v1/products/${productId}/image`, {
    method: "POST",
    headers: authHeader ? { "Authorization": authHeader } : {},
    body: formData,
  })
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw { response: { data: errorData } }
  }
  return response.json()
}

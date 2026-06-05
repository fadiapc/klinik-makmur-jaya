import { api } from "../lib/api"

export interface Role {
  id: number
  name: string
  description: string
}

export interface User {
  uuid: string
  name: string
  email: string
  phone: string | null
  is_active: boolean
  last_login_at: string | null
  role: Role
  created_at: string
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  page_size: number
}

export interface UserCreateData {
  name: string
  email: string
  password?: string
  role_id: number
  phone?: string
  is_active: boolean
}

export interface UserUpdateData {
  name?: string
  email?: string
  role_id?: number
  phone?: string
  is_active?: boolean
}

export interface UserFilterParams {
  q?: string
  role_id?: number
  is_active?: boolean
  page?: number
  page_size?: number
}

const ENDPOINT = "/users"

export async function fetchUsers(params: UserFilterParams): Promise<UserListResponse> {
  try {
    const response = await api.get<UserListResponse>(ENDPOINT, { params })
    return response.data
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Forbidden: Admin access required")
    }
    throw new Error(error.response?.data?.detail || "Failed to fetch users")
  }
}

export async function fetchRoles(): Promise<Role[]> {
  try {
    const response = await api.get<Role[]>(`${ENDPOINT}/roles/all`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || "Failed to fetch roles")
  }
}

export async function createUser(data: UserCreateData): Promise<User> {
  // Use default password if not provided
  if (!data.password) {
    data.password = "Klinik123!"
  }
  
  try {
    const response = await api.post<User>(ENDPOINT, data)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || "Failed to create user")
  }
}

export async function updateUser(uuid: string, data: UserUpdateData): Promise<User> {
  try {
    const response = await api.put<User>(`${ENDPOINT}/${uuid}`, data)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || "Failed to update user")
  }
}

export async function toggleUserStatus(uuid: string): Promise<User> {
  try {
    const response = await api.put<User>(`${ENDPOINT}/${uuid}/status`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || "Failed to toggle user status")
  }
}

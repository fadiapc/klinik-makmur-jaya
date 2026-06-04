import { create } from "zustand"
import { persist } from "zustand/middleware"

interface Role {
  id: number
  name: string
}

interface User {
  uuid: string
  email: string
  name: string
  role: Role
  is_verified: boolean
  is_active: boolean
  last_login_at: string | null
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    {
      name: "auth-storage", // keys for localStorage
    }
  )
)

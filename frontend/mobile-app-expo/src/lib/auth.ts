/**
 * [PHASE3] Adam Prism Mobile — Auth store
 * Token persistence with Zustand.
 */
import { create } from "zustand"
import * as SecureStore from "expo-secure-store"
import api from "./api"

interface User {
  id: string
  email?: string
  username?: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (usernameOrEmail: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loadStoredAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  async login(usernameOrEmail, password) {
    const tokens = await api.login(usernameOrEmail, password)
    set({
      user: { id: tokens.user_id, email: tokens.email, username: usernameOrEmail },
      isAuthenticated: true,
    })
  },

  async register(email, username, password) {
    const tokens = await api.register(email, username, password)
    set({
      user: { id: tokens.user_id, email, username },
      isAuthenticated: true,
    })
  },

  async logout() {
    await api.clearTokens()
    set({ user: null, isAuthenticated: false })
  },

  async loadStoredAuth() {
    try {
      const token = await SecureStore.getItemAsync("adam_access_token")
      if (token) {
        // Try to fetch user info
        const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          set({
            user: { id: data.user_id, email: data.email },
            isAuthenticated: true,
            isLoading: false,
          })
          return
        }
      }
    } catch {
      // ignore
    }
    set({ isLoading: false })
  },
}))

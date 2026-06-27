'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import Cookies from 'js-cookie'
import { login as apiLogin, register as apiRegister } from '@/lib/api'

interface User { id: number; email: string; name: string }
interface AuthCtx {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = Cookies.get('user')
    if (stored) { try { setUser(JSON.parse(stored)) } catch {} }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const { data } = await apiLogin({ email, password })
    Cookies.set('token', data.access_token, { expires: 7 })
    Cookies.set('user', JSON.stringify(data.user), { expires: 7 })
    setUser(data.user)
  }

  const register = async (name: string, email: string, password: string) => {
    const { data } = await apiRegister({ name, email, password })
    Cookies.set('token', data.access_token, { expires: 7 })
    Cookies.set('user', JSON.stringify(data.user), { expires: 7 })
    setUser(data.user)
  }

  const logout = () => {
    Cookies.remove('token')
    Cookies.remove('user')
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

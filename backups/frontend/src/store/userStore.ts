import { create } from 'zustand'

interface User {
    id: number
    telegram_id: number
    username: string
    phone: string
    age?: number
    gender?: string
    height?: number
    weight?: number
    goal?: string
    is_premium: boolean
    points: number
    referral_code: string
    premium_until?: string
}

interface UserState {
    user: User | null
    token: string | null
    setUser: (user: User) => void
    setToken: (token: string) => void
    logout: () => void
}

export const useUserStore = create<UserState>((set) => ({
    user: null,
    token: localStorage.getItem('token'),
    setUser: (user) => set({ user }),
    setToken: (token) => {
        localStorage.setItem('token', token)
        set({ token })
    },
    logout: () => {
        localStorage.removeItem('token')
        set({ user: null, token: null })
    }
}))

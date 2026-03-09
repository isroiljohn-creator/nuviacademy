import { useEffect, useState } from 'react'

import { Home as HomeIcon, Dumbbell, User, Shield } from 'lucide-react'
import { useUserStore } from './store/userStore'
import { authAPI } from './api/client'

import Home from './pages/Home'
import Plan from './pages/Plan'
import Profile from './pages/Profile'

import Premium from './pages/Premium'

function App() {
    const { token, setToken, setUser } = useUserStore()
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('home')

    useEffect(() => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready()
            window.Telegram.WebApp.expand()

            // Auth flow
            const initData = window.Telegram.WebApp.initData
            if (initData && !token) {
                authAPI.telegramAuth(initData)
                    .then((res) => {
                        setToken(res.data.token)
                        setUser(res.data.user)
                        setLoading(false)
                    })
                    .catch((err) => {
                        console.error('Auth failed', err)
                        setLoading(false)
                    })
            } else {
                setLoading(false)
            }
        } else {
            setLoading(false)
        }
    }, [])

    if (loading) {
        return <div className="flex items-center justify-center h-screen bg-black text-white">Yuklanmoqda...</div>
    }

    if (!token) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-black text-white p-4 text-center">
                <div className="text-red-500 text-xl mb-4">Kirish Xatosi</div>
                <p className="mb-4">
                    {!window.Telegram?.WebApp?.initData
                        ? "Iltimos, ushbu ilovani Telegram orqali oching."
                        : "Autentifikatsiya amalga oshmadi."}
                </p>
                {window.Telegram?.WebApp?.initData && (
                    <button
                        onClick={() => window.location.reload()}
                        className="bg-[#C8FF00] text-black px-4 py-2 rounded-lg font-bold"
                    >
                        Qayta urinish
                    </button>
                )}
                <div className="mt-8 text-xs text-gray-600">
                    Debug: {window.Telegram?.WebApp?.initData ? "initData present" : "No initData"}
                </div>
            </div>
        )
    }

    return (
        <div className="bg-black min-h-screen pb-20">
            {activeTab === 'home' && <Home />}
            {activeTab === 'plan' && <Plan />}
            {activeTab === 'premium' && <Premium />}
            {activeTab === 'profile' && <Profile />}

            {/* Navigation Bar */}
            <div className="fixed bottom-0 left-0 right-0 bg-[#111] border-t border-[#222] px-6 py-4 flex justify-between items-center z-50">
                <button
                    onClick={() => setActiveTab('home')}
                    className={`flex flex-col items-center gap-1 ${activeTab === 'home' ? 'text-[#E1FC00]' : 'text-gray-500'}`}
                >
                    <HomeIcon size={24} />
                    <span className="text-[10px] font-medium">Bosh sahifa</span>
                </button>

                <button
                    onClick={() => setActiveTab('plan')}
                    className={`flex flex-col items-center gap-1 ${activeTab === 'plan' ? 'text-[#E1FC00]' : 'text-gray-500'}`}
                >
                    <Dumbbell size={24} />
                    <span className="text-[10px] font-medium">Reja</span>
                </button>

                <button
                    onClick={() => setActiveTab('premium')}
                    className={`flex flex-col items-center gap-1 ${activeTab === 'premium' ? 'text-[#E1FC00]' : 'text-gray-500'}`}
                >
                    <Shield size={24} />
                    <span className="text-[10px] font-medium">Premium</span>
                </button>

                <button
                    onClick={() => setActiveTab('profile')}
                    className={`flex flex-col items-center gap-1 ${activeTab === 'profile' ? 'text-[#E1FC00]' : 'text-gray-500'}`}
                >
                    <User size={24} />
                    <span className="text-[10px] font-medium">Profil</span>
                </button>
            </div>
        </div>
    )
}

export default App

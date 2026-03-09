import { useEffect, useState } from 'react'
import { useUserStore } from '../store/userStore'
import { referralAPI } from '../api/client'
import { Copy, Gift, Users } from 'lucide-react'

export default function Profile() {
    const { user } = useUserStore()
    const [referralInfo, setReferralInfo] = useState<any>(null)

    useEffect(() => {
        const load = async () => {
            try {
                const res = await referralAPI.getInfo()
                setReferralInfo(res.data)
            } catch (error) {
                console.error(error)
            }
        }
        load()
    }, [])

    const copyLink = () => {
        if (referralInfo?.link) {
            navigator.clipboard.writeText(referralInfo.link)
            alert('Link nusxalandi!')
        }
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-3xl font-bold mb-6">Profil</h1>

            {/* User Info */}
            <div className="bg-[#1A1A1A] rounded-2xl p-6 mb-4">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-16 h-16 bg-[#C8FF00] rounded-full flex items-center justify-center text-black font-bold text-2xl">
                        {user?.username?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div>
                        <p className="font-bold text-xl">{user?.username || 'Foydalanuvchi'}</p>
                        {user?.is_premium && <span className="text-[#C8FF00] text-sm">⭐ Premium</span>}
                    </div>
                </div>
                <div className="space-y-2 text-sm text-gray-400">
                    <p>📱 Telefon: {user?.phone || 'N/A'}</p>
                    <p>Yosh: {user?.age || 'Belgilanmagan'}</p>
                    <p>Vazn: {user?.weight || '-'} kg</p>
                    <p>Bo'y: {user?.height || '-'} cm</p>
                    <p>Maqsad: {user?.goal || 'Belgilanmagan'}</p>
                </div>
            </div>

            {/* Referral Section */}
            <div className="bg-[#1A1A1A] rounded-2xl p-6 mb-4">
                <div className="flex items-center gap-2 mb-4">
                    <Users className="text-[#C8FF00]" />
                    <h2 className="text-xl font-bold">Referal</h2>
                </div>
                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <span className="text-gray-400">Do'stlar:</span>
                        <span className="font-bold">{referralInfo?.count || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-gray-400">Ballar:</span>
                        <span className="font-bold text-[#C8FF00]">{user?.points || 0}</span>
                    </div>
                    <button
                        onClick={copyLink}
                        className="w-full py-3 bg-[#C8FF00] text-black rounded-xl font-bold flex items-center justify-center gap-2"
                    >
                        <Copy size={20} />
                        Linkni Nusxalash
                    </button>
                </div>
            </div>

            {/* Premium Section */}
            {!user?.is_premium && (
                <div className="bg-gradient-to-r from-[#C8FF00]/20 to-[#C8FF00]/5 rounded-2xl p-6 border border-[#C8FF00]/30">
                    <div className="flex items-center gap-2 mb-3">
                        <Gift className="text-[#C8FF00]" />
                        <h2 className="text-xl font-bold">Premium Olish</h2>
                    </div>
                    <p className="text-sm text-gray-300 mb-4">
                        Barcha AI funksiyalar, cheksiz mashq va ovqat rejalari, kengaytirilgan statistika.
                    </p>
                    <button
                        onClick={() => {
                            // Navigate to internal premium page
                            window.location.hash = '#premium' // Using hash based routing or state change
                            // Since we use state-based routing in App.tsx, we can't easily switch tab from here without context.
                            // But wait, App.tsx passes activeTab. 
                            // Actually, let's just use a custom event or reload for now, OR better:
                            // The userStore doesn't control navigation.
                            // Let's use a simple hack: dispatch a custom event that App.tsx listens to, or just reload with a query param?
                            // No, let's just fix App.tsx to expose a navigation method or use a global event.
                            // For now, let's try to dispatch a custom event 'navigate-to-premium'
                            window.dispatchEvent(new CustomEvent('navigate-to-premium'))
                        }}
                        className="w-full py-3 bg-[#C8FF00] text-black rounded-xl font-bold"
                    >
                        Premium Sotib Olish
                    </button>
                </div>
            )}
        </div>
    )
}

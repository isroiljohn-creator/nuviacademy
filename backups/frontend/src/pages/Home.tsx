import { useEffect, useState } from 'react'
import { useUserStore } from '../store/userStore'
import { userAPI } from '../api/client'
import { Activity, Dumbbell, Utensils } from 'lucide-react'

export default function Home() {
    const { user, setUser } = useUserStore()
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const loadUser = async () => {
            try {
                const res = await userAPI.getProfile()
                setUser(res.data)
            } catch (error) {
                console.error('Failed to load user', error)
            } finally {
                setLoading(false)
            }
        }
        loadUser()
    }, [])

    if (loading) {
        return <div className="flex items-center justify-center h-screen bg-black text-white">Yuklanmoqda...</div>
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Salom, {user?.username || 'Foydalanuvchi'}</h1>
                <p className="text-gray-400">Bugungi maqsadlaringizni bajaring</p>
            </div>

            {/* Today's Tasks */}
            <div className="bg-[#1A1A1A] rounded-2xl p-6 mb-6">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Activity className="text-[#C8FF00]" />
                    Bugungi Vazifalar
                </h2>
                <div className="space-y-3">
                    <TaskItem label="2 litr suv ichish" completed={false} />
                    <TaskItem label="Mashq qilish" completed={false} />
                    <TaskItem label="10k qadam yurish" completed={false} />
                </div>
            </div>

            {/* Quick Access */}
            <div className="grid grid-cols-2 gap-4">
                <QuickCard icon={<Dumbbell />} title="Mashq Rejasi" color="#C8FF00" />
                <QuickCard icon={<Utensils />} title="Ovqat Rejasi" color="#C8FF00" />
            </div>

            {/* Premium Badge */}
            {!user?.is_premium && (
                <div className="mt-6 bg-gradient-to-r from-[#C8FF00]/20 to-[#C8FF00]/5 rounded-2xl p-4 border border-[#C8FF00]/30">
                    <p className="text-sm font-medium text-[#C8FF00]">
                        ⭐ Premiumga o'ting va barcha imkoniyatlardan foydalaning
                    </p>
                </div>
            )}
        </div>
    )
}

function TaskItem({ label, completed }: { label: string, completed: boolean }) {
    return (
        <div className="flex items-center gap-3">
            <div className={`w-6 h-6 rounded-full border-2 ${completed ? 'bg-[#C8FF00] border-[#C8FF00]' : 'border-gray-600'}`} />
            <span className={completed ? 'line-through text-gray-500' : ''}>{label}</span>
        </div>
    )
}

function QuickCard({ icon, title, color }: { icon: React.ReactNode, title: string, color: string }) {
    return (
        <div className="bg-[#1A1A1A] rounded-2xl p-6 flex flex-col items-center gap-3 hover:bg-[#2A2A2A] transition-all cursor-pointer">
            <div style={{ color }}>{icon}</div>
            <span className="text-sm font-medium">{title}</span>
        </div>
    )
}

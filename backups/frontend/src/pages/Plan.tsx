import { useState } from 'react'
import { aiAPI } from '../api/client'
import { Dumbbell, Utensils, Loader2 } from 'lucide-react'

export default function Plan() {
    const [tab, setTab] = useState<'workout' | 'meal'>('workout')
    const [workout, setWorkout] = useState('')
    const [meal, setMeal] = useState('')
    const [loading, setLoading] = useState(false)

    const loadWorkout = async () => {
        setLoading(true)
        try {
            const res = await aiAPI.generateWorkout()
            setWorkout(res.data.plan)
        } catch (error) {
            console.error(error)
            setWorkout('Xatolik yuz berdi')
        } finally {
            setLoading(false)
        }
    }

    const loadMeal = async () => {
        setLoading(true)
        try {
            const res = await aiAPI.generateMeal()
            setMeal(res.data.plan)
        } catch (error) {
            console.error(error)
            setMeal('Xatolik yuz berdi')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-3xl font-bold mb-6">Mening Rejam</h1>

            {/* Tabs */}
            <div className="flex gap-4 mb-6">
                <button
                    onClick={() => setTab('workout')}
                    className={`flex-1 py-3 rounded-xl font-medium transition-all ${tab === 'workout' ? 'bg-[#C8FF00] text-black' : 'bg-[#1A1A1A] text-white'
                        }`}
                >
                    <Dumbbell className="inline mr-2" size={20} />
                    Mashq
                </button>
                <button
                    onClick={() => setTab('meal')}
                    className={`flex-1 py-3 rounded-xl font-medium transition-all ${tab === 'meal' ? 'bg-[#C8FF00] text-black' : 'bg-[#1A1A1A] text-white'
                        }`}
                >
                    <Utensils className="inline mr-2" size={20} />
                    Ovqat
                </button>
            </div>

            {/* Content */}
            <div className="bg-[#1A1A1A] rounded-2xl p-6">
                {tab === 'workout' ? (
                    <div>
                        {!workout ? (
                            <button
                                onClick={loadWorkout}
                                disabled={loading}
                                className="w-full py-4 bg-[#C8FF00] text-black rounded-xl font-bold flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="animate-spin" /> : 'Rejani Olish'}
                            </button>
                        ) : (
                            <div className="prose prose-invert max-w-none">
                                <pre className="whitespace-pre-wrap text-sm">{workout}</pre>
                            </div>
                        )}
                    </div>
                ) : (
                    <div>
                        {!meal ? (
                            <button
                                onClick={loadMeal}
                                disabled={loading}
                                className="w-full py-4 bg-[#C8FF00] text-black rounded-xl font-bold flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="animate-spin" /> : 'Menyuni Olish'}
                            </button>
                        ) : (
                            <div className="prose prose-invert max-w-none">
                                <pre className="whitespace-pre-wrap text-sm">{meal}</pre>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

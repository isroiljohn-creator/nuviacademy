import { useUserStore } from '../store/userStore'

export default function Premium() {
    const { user } = useUserStore()

    const handlePurchasePremium = () => {
        // Redirect to Telegram bot for premium purchase
        window.location.href = 'https://t.me/Yasha_UzBot?start=premium'
    }

    if (user?.is_premium) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[80vh] p-6">
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4">💎</div>
                    <h1 className="text-3xl font-bold mb-2">Premium Aktiv!</h1>
                    <p className="text-gray-400">
                        Sizning obunangiz {new Date(user.premium_until || '').toLocaleDateString()} gacha amal qiladi.
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-4 w-full max-w-md">
                    <div className="bg-zinc-800 p-4 rounded-lg text-center">
                        <div className="text-3xl mb-2">🤖</div>
                        <p className="text-sm font-semibold">AI Rejalar</p>
                    </div>
                    <div className="bg-zinc-800 p-4 rounded-lg text-center">
                        <div className="text-3xl mb-2">📊</div>
                        <p className="text-sm font-semibold">Tahlil</p>
                    </div>
                    <div className="bg-zinc-800 p-4 rounded-lg text-center">
                        <div className="text-3xl mb-2">🍽</div>
                        <p className="text-sm font-semibold">Allergiya yo'q</p>
                    </div>
                    <div className="bg-zinc-800 p-4 rounded-lg text-center">
                        <div className="text-3xl mb-2">💪</div>
                        <p className="text-sm font-semibold">Individual</p>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] p-6">
            <div className="text-center mb-8">
                <div className="text-6xl mb-4">💎</div>
                <h1 className="text-3xl font-bold mb-2">Premium Olish</h1>
                <p className="text-gray-400">Individual AI rejalar va ko'proq imkoniyatlar</p>
            </div>

            {/* Features */}
            <div className="grid grid-cols-2 gap-4 w-full max-w-md mb-8">
                <div className="bg-zinc-800 p-4 rounded-lg text-center">
                    <div className="text-3xl mb-2">🤖</div>
                    <p className="text-sm font-semibold">AI Individual Rejalar</p>
                </div>
                <div className="bg-zinc-800 p-4 rounded-lg text-center">
                    <div className="text-3xl mb-2">🍽</div>
                    <p className="text-sm font-semibold">Allergiyaga mos</p>
                </div>
                <div className="bg-zinc-800 p-4 rounded-lg text-center">
                    <div className="text-3xl mb-2">📊</div>
                    <p className="text-sm font-semibold">Tahlil va Statistika</p>
                </div>
                <div className="bg-zinc-800 p-4 rounded-lg text-center">
                    <div className="text-3xl mb-2">💪</div>
                    <p className="text-sm font-semibold">Shaxsiy Yondashuv</p>
                </div>
            </div>

            {/* Pricing */}
            <div className="w-full max-w-md space-y-4 mb-8">
                <div className="bg-gradient-to-r from-[#C8FF00]/20 to-transparent p-6 rounded-lg border border-[#C8FF00]/30">
                    <div className="flex justify-between items-center">
                        <div>
                            <h3 className="text-xl font-bold">1 oy</h3>
                            <p className="text-gray-400 text-sm">Barcha imkoniyatlar</p>
                        </div>
                        <div className="text-2xl font-bold text-[#C8FF00]">49 000 so'm</div>
                    </div>
                </div>

                <div className="bg-gradient-to-r from-[#C8FF00]/30 to-transparent p-6 rounded-lg border-2 border-[#C8FF00]">
                    <div className="absolute -top-3 left-4 bg-[#C8FF00] text-black px-3 py-1 rounded-full text-xs font-bold">
                        MASHHUR
                    </div>
                    <div className="flex justify-between items-center">
                        <div>
                            <h3 className="text-xl font-bold">3 oy</h3>
                            <p className="text-gray-400 text-sm">23% tejang</p>
                        </div>
                        <div className="text-2xl font-bold text-[#C8FF00]">119 000 so'm</div>
                    </div>
                </div>
            </div>

            {/* Purchase Button */}
            <button
                onClick={handlePurchasePremium}
                className="w-full max-w-md bg-[#C8FF00] text-black font-bold py-4 px-8 rounded-lg hover:bg-[#D4FF33] transition-all transform hover:scale-105"
            >
                💳 Premium Sotib Olish
            </button>

            {/* Redirect note */}
            <p className="text-gray-500 text-sm mt-4 text-center max-w-md">
                📱 Siz botga yo'naltirilasiz. U yerda to'lovni amalga oshiring.
            </p>
        </div>
    )
}

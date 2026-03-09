import { useEffect, useState } from 'react'
import { initPayment, getProfile, type PaymentInit, type UserProfile } from '../api/client'

export default function Payment() {
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [payment, setPayment] = useState<PaymentInit | null>(null)
    const [loading, setLoading] = useState(true)
    const [processing, setProcessing] = useState(false)
    const [provider, setProvider] = useState('click')

    useEffect(() => {
        getProfile()
            .then(setProfile)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    const handlePayment = async () => {
        setProcessing(true)
        try {
            const result = await initPayment(provider)
            setPayment(result)
            // Redirect to payment page
            window.open(result.payment_url, '_blank')
        } catch {
            alert('Xatolik yuz berdi. Qayta urinib ko\'ring.')
        } finally {
            setProcessing(false)
        }
    }

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>
    }

    if (profile?.subscription_status === 'active') {
        return (
            <div className="page">
                <h1 className="page-title">💎 Obuna</h1>
                <div className="card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 64, marginBottom: 16 }}>🎉</div>
                    <h2 style={{ marginBottom: 8 }}>Obunangiz faol!</h2>
                    <p style={{ color: 'var(--tg-hint)', fontSize: 14 }}>
                        Barcha klub imkoniyatlaridan foydalanishingiz mumkin.
                    </p>
                </div>
            </div>
        )
    }

    const basePrice = 97_000
    const formatPrice = (n: number) => n.toLocaleString('uz-UZ').replace(/,/g, ' ')

    return (
        <div className="page">
            <h1 className="page-title">💎 Klubga a'zo bo'lish</h1>

            {/* Price Card */}
            <div className="card">
                <div className="price-display">
                    {payment && payment.referral_discount > 0 && (
                        <div className="price-original">{formatPrice(basePrice)} so'm</div>
                    )}
                    <div className="price-final">
                        {formatPrice(payment?.final_price || basePrice)} so'm
                    </div>
                    <div className="price-label">oyiga</div>
                    {payment && payment.referral_discount > 0 && (
                        <div className="discount-badge">
                            🎁 Taklif chegirmasi: -{formatPrice(payment.referral_discount)} so'm
                        </div>
                    )}
                </div>
            </div>

            {/* Benefits */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">✨</span>
                    <span className="card-title">Imkoniyatlar</span>
                </div>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {[
                        'AI bilan pul topish strategiyalari',
                        'Shaxsiy mentor yordami',
                        'Haftalik live darslar',
                        'Tayyor shablonlar va promptlar',
                        'Ekskluziv hamjamiyat',
                    ].map((item, i) => (
                        <li key={i} style={{
                            padding: '10px 0',
                            borderBottom: i < 4 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                            display: 'flex',
                            gap: 8,
                            alignItems: 'center',
                        }}>
                            <span style={{ color: '#34d399' }}>✅</span>
                            <span style={{ fontSize: 14 }}>{item}</span>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Payment Provider Selection */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">💳</span>
                    <span className="card-title">To'lov usuli</span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    {['click', 'payme'].map(p => (
                        <button
                            key={p}
                            onClick={() => setProvider(p)}
                            style={{
                                flex: 1,
                                padding: '14px',
                                borderRadius: 'var(--radius-sm)',
                                border: `2px solid ${provider === p ? 'var(--tg-link)' : 'rgba(255,255,255,0.1)'}`,
                                background: provider === p ? 'rgba(108, 99, 255, 0.15)' : 'transparent',
                                color: 'var(--tg-text)',
                                cursor: 'pointer',
                                fontWeight: 700,
                                fontSize: 15,
                                transition: 'all 0.2s',
                            }}
                        >
                            {p === 'click' ? '🟢 Click' : '🔵 Payme'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Pay Button */}
            <button
                className="btn btn-primary"
                onClick={handlePayment}
                disabled={processing}
                style={{ marginTop: 8 }}
            >
                {processing ? '⏳ Yuklanmoqda...' : `💳 To'lov qilish — ${formatPrice(basePrice)} so'm`}
            </button>

            <p style={{
                textAlign: 'center',
                fontSize: 12,
                color: 'var(--tg-hint)',
                marginTop: 12,
            }}>
                🔒 Xavfsiz to'lov. Istalgan vaqt bekor qilish mumkin.
            </p>
        </div>
    )
}

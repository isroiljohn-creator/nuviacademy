import { useEffect, useState } from 'react'
import { getReferralStats, type ReferralStats } from '../api/client'

export default function Referral() {
    const [stats, setStats] = useState<ReferralStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [copied, setCopied] = useState(false)

    useEffect(() => {
        getReferralStats()
            .then(setStats)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    const copyLink = async () => {
        if (!stats) return
        try {
            await navigator.clipboard.writeText(stats.referral_link)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch {
            // Fallback for environments without clipboard API
            const input = document.createElement('input')
            input.value = stats.referral_link
            document.body.appendChild(input)
            input.select()
            document.execCommand('copy')
            document.body.removeChild(input)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>
    }

    if (!stats) {
        return (
            <div className="page">
                <p style={{ textAlign: 'center', color: 'var(--tg-hint)' }}>
                    Ma'lumotlar yuklanmadi
                </p>
            </div>
        )
    }

    const formatPrice = (n: number) => n.toLocaleString('uz-UZ').replace(/,/g, ' ')

    // Progress towards free subscription
    const progressToFree = stats.club_price > 0
        ? Math.min(100, ((stats.club_price - stats.amount_for_free) / stats.club_price) * 100)
        : 0

    return (
        <div className="page">
            <h1 className="page-title">🔗 Taklif dasturi</h1>

            {/* Referral Link */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">📎</span>
                    <span className="card-title">Sizning havolangiz</span>
                </div>
                <div className="referral-link-box" onClick={copyLink}>
                    {stats.referral_link}
                </div>
                <button
                    className="btn btn-primary"
                    onClick={copyLink}
                    style={{ marginTop: 12 }}
                >
                    {copied ? '✅ Nusxalandi!' : '📋 Havolani nusxalash'}
                </button>
            </div>

            {/* Stats Grid */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">📊</span>
                    <span className="card-title">Statistika</span>
                </div>
                <div className="stats-grid">
                    <div className="stat-item">
                        <div className="stat-value">{stats.total_invited}</div>
                        <div className="stat-label">Jami taklif</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{stats.valid_referrals}</div>
                        <div className="stat-label">Tasdiqlangan</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{stats.paid_referrals}</div>
                        <div className="stat-label">To'langan</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ fontSize: 18 }}>
                            {formatPrice(stats.balance)}
                        </div>
                        <div className="stat-label">Balans (so'm)</div>
                    </div>
                </div>
            </div>

            {/* Progress to Free Subscription */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">🎯</span>
                    <span className="card-title">Bepul obunaga yo'l</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                    <span>{formatPrice(stats.club_price - stats.amount_for_free)} / {formatPrice(stats.club_price)} so'm</span>
                    <span style={{ fontWeight: 700 }}>{Math.round(progressToFree)}%</span>
                </div>
                <div className="progress-bar">
                    <div
                        className="progress-fill gold"
                        style={{ width: `${progressToFree}%` }}
                    />
                </div>

                {stats.amount_for_free > 0 ? (
                    <p style={{ fontSize: 13, color: 'var(--tg-hint)', marginTop: 8 }}>
                        Bepul obuna uchun yana {formatPrice(stats.amount_for_free)} so'm kerak.
                        Do'stlaringizni taklif qiling! 🚀
                    </p>
                ) : (
                    <p style={{ fontSize: 13, color: '#34d399', marginTop: 8, fontWeight: 700 }}>
                        🎉 Bepul obuna olish uchun yetarli balans bor!
                    </p>
                )}
            </div>

            {/* How it works */}
            <div className="card">
                <div className="card-header">
                    <span className="card-icon">ℹ️</span>
                    <span className="card-title">Qanday ishlaydi?</span>
                </div>
                <ol style={{ paddingLeft: 20, fontSize: 14, lineHeight: 2, color: 'var(--tg-hint)' }}>
                    <li>Havolani do'stlaringizga yuboring</li>
                    <li>Ular ro'yxatdan o'tsin</li>
                    <li>Telefon raqamini yuborsin</li>
                    <li>Lead magnet ochsin</li>
                    <li>Siz mukofot olasiz! 🎁</li>
                </ol>
            </div>
        </div>
    )
}

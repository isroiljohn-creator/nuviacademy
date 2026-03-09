import { useEffect, useState } from 'react'
import { getCourseModules, updateProgress, type CourseModule } from '../api/client'

export default function Course() {
    const [modules, setModules] = useState<CourseModule[]>([])
    const [loading, setLoading] = useState(true)
    const [activeModule, setActiveModule] = useState<CourseModule | null>(null)

    useEffect(() => {
        getCourseModules()
            .then(setModules)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    const handleModuleClick = (mod: CourseModule) => {
        if (mod.is_locked) return
        setActiveModule(mod)
    }

    const handleComplete = async (mod: CourseModule) => {
        try {
            await updateProgress(mod.id, 300, 100)
            // Refresh modules
            const updated = await getCourseModules()
            setModules(updated)
            setActiveModule(null)
        } catch {
            alert('Xatolik yuz berdi')
        }
    }

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>
    }

    // Calculate overall progress
    const totalModules = modules.length
    const completedModules = modules.filter(m => m.is_completed).length
    const overallProgress = totalModules > 0 ? (completedModules / totalModules) * 100 : 0

    // Active module view
    if (activeModule) {
        return (
            <div className="page">
                <button
                    onClick={() => setActiveModule(null)}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--tg-link)',
                        fontSize: 15,
                        cursor: 'pointer',
                        marginBottom: 16,
                        fontWeight: 600,
                    }}
                >
                    ← Orqaga
                </button>

                <h1 className="page-title">{activeModule.title}</h1>

                {activeModule.video_url && (
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <video
                            src={activeModule.video_url}
                            controls
                            style={{ width: '100%', borderRadius: 'var(--radius)' }}
                            playsInline
                        />
                    </div>
                )}

                {activeModule.description && (
                    <div className="card">
                        <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--tg-hint)' }}>
                            {activeModule.description}
                        </p>
                    </div>
                )}

                {/* Progress */}
                <div className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                        <span>Jarayon</span>
                        <span style={{ fontWeight: 700 }}>{Math.round(activeModule.completion_pct)}%</span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill purple"
                            style={{ width: `${activeModule.completion_pct}%` }}
                        />
                    </div>
                </div>

                {!activeModule.is_completed && (
                    <button
                        className="btn btn-success"
                        onClick={() => handleComplete(activeModule)}
                    >
                        ✅ Modulni tugatish
                    </button>
                )}

                {activeModule.is_completed && (
                    <div style={{
                        textAlign: 'center',
                        padding: 20,
                        color: '#34d399',
                        fontWeight: 700,
                    }}>
                        ✅ Modul tugatilgan
                    </div>
                )}
            </div>
        )
    }

    // Module list view
    return (
        <div className="page">
            <h1 className="page-title">📚 Bepul kurs</h1>

            {/* Overall progress */}
            <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                    <span>Umumiy progress</span>
                    <span style={{ fontWeight: 700 }}>{completedModules}/{totalModules} modul</span>
                </div>
                <div className="progress-bar">
                    <div
                        className="progress-fill green"
                        style={{ width: `${overallProgress}%` }}
                    />
                </div>
            </div>

            {/* Module list */}
            {modules.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--tg-hint)', padding: 40 }}>
                    Hozircha modullar qo'shilmagan
                </div>
            ) : (
                modules.map((mod) => (
                    <div
                        key={mod.id}
                        className={`module-item ${mod.is_locked ? 'locked' : ''} ${mod.is_completed ? 'completed' : ''}`}
                        onClick={() => handleModuleClick(mod)}
                    >
                        <div className={`module-number ${mod.is_completed ? 'completed' : mod.is_locked ? 'locked' : 'active'}`}>
                            {mod.is_completed ? '✓' : mod.is_locked ? '🔒' : mod.order}
                        </div>
                        <div className="module-info">
                            <div className="module-title">{mod.title}</div>
                            <div className="module-status">
                                {mod.is_completed
                                    ? '✅ Tugatilgan'
                                    : mod.is_locked
                                        ? '🔒 Qulflangan'
                                        : mod.completion_pct > 0
                                            ? `▶️ ${Math.round(mod.completion_pct)}% ko'rilgan`
                                            : '📖 Boshlash'
                                }
                            </div>
                        </div>
                    </div>
                ))
            )}

            {completedModules === totalModules && totalModules > 0 && (
                <div className="card" style={{ textAlign: 'center', marginTop: 16 }}>
                    <div style={{ fontSize: 48, marginBottom: 8 }}>🎉</div>
                    <h3>Tabriklaymiz!</h3>
                    <p style={{ color: 'var(--tg-hint)', fontSize: 14, marginTop: 8 }}>
                        Barcha modullarni tugatdingiz.
                    </p>
                </div>
            )}
        </div>
    )
}

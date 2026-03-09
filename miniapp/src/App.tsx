import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { useEffect } from 'react'
import Payment from './pages/Payment'
import Course from './pages/Course'
import Dashboard from './pages/Dashboard'
import Referral from './pages/Referral'

export default function App() {
    useEffect(() => {
        // Initialize Telegram WebApp
        window.Telegram?.WebApp?.ready()
        window.Telegram?.WebApp?.expand()
    }, [])

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/payment" element={<Payment />} />
                <Route path="/course" element={<Course />} />
                <Route path="/referral" element={<Referral />} />
            </Routes>

            {/* Bottom Navigation */}
            <nav className="bottom-nav">
                <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <span className="nav-icon">🏠</span>
                    Bosh sahifa
                </NavLink>
                <NavLink to="/course" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <span className="nav-icon">📚</span>
                    Kurs
                </NavLink>
                <NavLink to="/payment" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <span className="nav-icon">💎</span>
                    Obuna
                </NavLink>
                <NavLink to="/referral" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <span className="nav-icon">🔗</span>
                    Taklif
                </NavLink>
            </nav>
        </BrowserRouter>
    )
}

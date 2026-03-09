/**
 * API client for Mini App ↔ Backend communication.
 * All requests include Telegram initData for authentication.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

function getInitData(): string {
    return window.Telegram?.WebApp?.initData || '';
}

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-Telegram-Init-Data': getInitData(),
            ...options?.headers,
        },
    });

    if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
    }

    return res.json();
}

// ── User ──
export interface UserProfile {
    telegram_id: number;
    name: string | null;
    age: number | null;
    goal_tag: string | null;
    level_tag: string | null;
    lead_score: number;
    lead_segment: string;
    user_status: string;
    subscription_status: string;
    registered_at: string | null;
}

export function getProfile(): Promise<UserProfile> {
    return apiRequest('/user/profile');
}

// ── Referral ──
export interface ReferralStats {
    referral_link: string;
    total_invited: number;
    valid_referrals: number;
    paid_referrals: number;
    balance: number;
    club_price: number;
    amount_for_free: number;
}

export function getReferralStats(): Promise<ReferralStats> {
    return apiRequest('/referral/stats');
}

// ── Payment ──
export interface PaymentInit {
    payment_id: number;
    base_price: number;
    referral_discount: number;
    final_price: number;
    payment_url: string;
}

export function initPayment(provider: string = 'click'): Promise<PaymentInit> {
    return apiRequest('/payment/init', {
        method: 'POST',
        body: JSON.stringify({ provider }),
    });
}

// ── Course ──
export interface CourseModule {
    id: number;
    title: string;
    description: string | null;
    video_url: string | null;
    order: number;
    is_locked: boolean;
    completion_pct: number;
    is_completed: boolean;
}

export function getCourseModules(): Promise<CourseModule[]> {
    return apiRequest('/course/modules');
}

export function updateProgress(moduleId: number, watchTime: number, completionPct: number): Promise<void> {
    return apiRequest('/course/progress', {
        method: 'POST',
        body: JSON.stringify({
            module_id: moduleId,
            watch_time: watchTime,
            completion_pct: completionPct,
        }),
    });
}

// ── Telegram WebApp types ──
declare global {
    interface Window {
        Telegram?: {
            WebApp?: {
                initData: string;
                initDataUnsafe: {
                    user?: { id: number; first_name: string };
                };
                ready: () => void;
                close: () => void;
                expand: () => void;
                MainButton: {
                    text: string;
                    show: () => void;
                    hide: () => void;
                    onClick: (fn: () => void) => void;
                    enable: () => void;
                    disable: () => void;
                };
                themeParams: Record<string, string>;
            };
        };
    }
}

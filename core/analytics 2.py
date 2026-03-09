import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from datetime import datetime, timedelta
# from core.db import db # Removed incorrect import
from backend.database import get_sync_db # Import specifically
from sqlalchemy import text

from sqlalchemy import text

def _get_buffer():
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def get_growth_stats():
    """Returns (report_text, chart_bytes) for growth."""
    with get_sync_db() as session:
        # DAU Last 7 days
        sql = """
        SELECT date_trunc('day', created_at) as day, count(distinct user_id) as users
        FROM event_logs
        WHERE created_at >= now() - interval '7 days'
        GROUP BY 1 ORDER BY 1
        """
        data = session.execute(text(sql)).fetchall()
        
        dates = [r[0].strftime('%d/%m') for r in data]
        counts = [r[1] for r in data]
        
        plt.figure(figsize=(6, 4))
        plt.plot(dates, counts, marker='o', color='#4CAF50')
        plt.title('DAU (Last 7 Days)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        chart = _get_buffer()
        
        report = "📈 **Growth Stats**\n\n"
        report += f"Bugungi DAU: {counts[-1] if counts else 0}\n"
        avg_dau = int(sum(counts)/len(counts)) if counts else 0
        report += f"O'tgan haftadagi o'rtacha: {avg_dau}"
        
        return report, chart

def get_funnel_stats():
    """Returns (report_text, chart_bytes) for funnel."""
    with get_sync_db() as session:
        sql = """
        SELECT event_type, count(distinct user_id)
        FROM event_logs
        WHERE event_type IN ('bot_start', 'onboarding_completed', 'trial_started')
        AND created_at >= now() - interval '30 days'
        GROUP BY 1
        """
        data = dict(session.execute(text(sql)).fetchall())
        
        labels = ['Start', 'Onboarded', 'Trial']
        values = [data.get('bot_start', 0), data.get('onboarding_completed', 0), data.get('trial_started', 0)]
        
        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color='#2196F3')
        plt.title('User Funnel (30 Days)')
        plt.tight_layout()
        chart = _get_buffer()
        
        conv = round(values[1]/values[0]*100, 1) if values[0] > 0 else 0
        report = "🌪 **Funnel Stats**\n\n"
        report += f"Start -> Onboarded: {conv}%\n"
        report += f"Jami onboarded: {values[1]}"
        
        return report, chart

def get_retention_stats():
    """Returns (report_text, chart_bytes) for retention."""
    with get_sync_db() as session:
        sql = """
            WITH cohort AS (
                SELECT user_id, MIN(date_trunc('day', created_at)) AS day0
                FROM event_logs
                WHERE event_type = 'onboarding_completed' AND created_at >= now() - interval '30 days'
                GROUP BY 1
            ),
            activity AS (
                SELECT DISTINCT user_id, date_trunc('day', created_at) AS day
                FROM event_logs
                WHERE created_at >= now() - interval '30 days'
            )
            SELECT
                ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '1 day') THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d1,
                ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '3 day') THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d3,
                ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '7 day') THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d7
            FROM cohort c
        """
        res = session.execute(text(sql)).fetchone()
        d1, d3, d7 = (res[0] or 0, res[1] or 0, res[2] or 0) if res else (0,0,0)
        
        labels = ['D1', 'D3', 'D7']
        values = [d1, d3, d7]
        
        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color=['#4CAF50', '#FFC107', '#F44336'])
        plt.title('Retention Rates (%)')
        plt.ylim(0, 100)
        plt.tight_layout()
        chart = _get_buffer()
        
        report = "📉 **Retention Stats**\n\n"
        report += f"Day 1: {d1}%\nDay 3: {d3}%\nDay 7: {d7}%"
        
        return report, chart

def get_premium_stats():
    """Returns (report_text, chart_bytes) for premium."""
    with get_sync_db() as session:
        sql = """
        SELECT 
            (SELECT count(*) FROM users WHERE is_premium = true) as total_premium,
            (SELECT count(*) FROM event_logs WHERE event_type = 'premium_activated' AND created_at >= now() - interval '30 days') as new_premium_30d
        """
        res = session.execute(text(sql)).fetchone()
        total, new_30 = (res[0] or 0, res[1] or 0) if res else (0,0)
        
        report = "💎 **Premium Stats**\n\n"
        report += f"Jami Premium userlar: {total}\n"
        report += f"Oxirgi 30 kunda yangi: {new_30}"
        
        # Simple dummy chart for premium (maybe pie chart of free vs premium)
        sql2 = "SELECT count(*) FROM users"
        total_users = session.execute(text(sql2)).scalar() or 1
        free = total_users - total
        
        plt.figure(figsize=(6, 4))
        plt.pie([total, free], labels=['Premium', 'Free'], autopct='%1.1f%%', colors=['#FFD700', '#C0C0C0'])
        plt.title('Premium vs Free Users')
        plt.tight_layout()
        chart = _get_buffer()
        
        return report, chart

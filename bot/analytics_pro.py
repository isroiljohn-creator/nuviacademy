from telebot import types
from sqlalchemy import text
from backend.database import get_sync_db
from core.db import db
from datetime import datetime, timedelta

def register_analytics_handlers(bot):
    
    @bot.message_handler(commands=['analytics_pro'])
    def analytics_pro_cmd(message):
        # Admin check handled by safe_handler wrapper usually, but let's do explicit check here too
        # assuming ADMIN_IDS is imported or passed. 
        # Better: let's import ADMIN_IDS from config or main.
        # For valid implementation, we assume caller handles auth or we do it here.
        # We'll use a local check.
        from core.config import ADMIN_IDS
        if message.from_user.id not in ADMIN_IDS:
            return

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("📌 Investor Snapshot", callback_data="opro:investor"))
        markup.row(types.InlineKeyboardButton("🧠 Feedback & Adaptation", callback_data="opro:adapt"))
        markup.row(types.InlineKeyboardButton("💸 AI Cost & Savings", callback_data="opro:cost"))
        markup.row(types.InlineKeyboardButton("⚙️ System Optimization", callback_data="opro:opt"))
        
        # Add Mini App Button
        import os
        base_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
        # Ensure base_url doesn't have a trailing slash for concatenation
        if base_url.endswith("/"): base_url = base_url[:-1]
        webapp_url = f"{base_url}/admin-insights/"
        
        markup.row(types.InlineKeyboardButton("📊 Admin Dashboard", web_app=types.WebAppInfo(url=webapp_url)))
        
        bot.send_message(
            message.chat.id,
            "📊 <b>YASHA Analytics Pro</b>\nSelect a dashboard section:",
            parse_mode="HTML",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("opro:"))
    def handle_analytics_callback(call):
        from core.config import ADMIN_IDS
        if call.from_user.id not in ADMIN_IDS:
             bot.answer_callback_query(call.id, "Access denied")
             return

        action = call.data.split(":")[1]
        
        try:
            if action == "investor":
                report = get_investor_snapshot(7)
                bot.edit_message_text(report, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_back_markup())
            
            elif action == "adapt":
                report = get_feedback_adaptation_report()
                bot.edit_message_text(report, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_back_markup())
            
            elif action == "cost":
                report = get_ai_cost_report()
                bot.edit_message_text(report, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_back_markup())
            
            elif action == "opt":
                report = get_optimization_report()
                bot.edit_message_text(report, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_back_markup())

            elif action == "menu":
                # Restore main menu
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("📌 Investor Snapshot", callback_data="opro:investor"))
                markup.row(types.InlineKeyboardButton("🧠 Feedback & Adaptation", callback_data="opro:adapt"))
                markup.row(types.InlineKeyboardButton("💸 AI Cost & Savings", callback_data="opro:cost"))
                markup.row(types.InlineKeyboardButton("⚙️ System Optimization", callback_data="opro:opt"))
                bot.edit_message_text("📊 <b>YASHA Analytics Pro</b>\nSelect a dashboard section:", 
                                     call.message.chat.id, call.message.message_id, 
                                     parse_mode="HTML", reply_markup=markup)

        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {e}")
            import traceback
            traceback.print_exc()

# ... (keep existing helper) ...

def get_optimization_report():
    with get_sync_db() as session:
        # 1. Feature Flag Status
        from backend.models import FeatureFlag, OptimizationLog, DishReviewQueue
        flag = session.get(FeatureFlag, 'optimization_v1')
        status = "✅ ON" if flag and flag.enabled else "🔴 OFF"
        
        # 2. Optimization Logs (7d)
        log_sql = text("""
            SELECT action, COUNT(*) 
            FROM optimization_logs 
            WHERE created_at >= now() - interval '7 days' 
            GROUP BY 1 ORDER BY 2 DESC
        """)
        logs = session.execute(log_sql).fetchall()
        log_str = "\n".join([f"• {r[0]}: {r[1]}" for r in logs]) or "No actions yet"
        
        # 3. Review Queue Check
        q_sql = text("""
            SELECT reason, COUNT(*) 
            FROM dish_review_queue 
            WHERE status='open' 
            GROUP BY 1 ORDER BY 2 DESC LIMIT 3
        """)
        queue = session.execute(q_sql).fetchall()
        queue_str = "\n".join([f"• {r[0]}: {r[1]}" for r in queue]) or "Queue empty"
        
        # 4. Adaptation Effectiveness Rate
        eff_sql = text("""
            SELECT 
                COUNT(DISTINCT bad.user_id) as total_bad,
                COUNT(DISTINCT good.user_id) as improved
            FROM (
                SELECT user_id, min(created_at) as first_bad
                FROM menu_feedback
                WHERE rating='bad' AND created_at >= now() - interval '7 days'
                GROUP BY user_id
            ) bad
            LEFT JOIN menu_feedback good ON good.user_id = bad.user_id
                AND good.created_at > bad.first_bad
                AND good.rating IN ('good', 'ok')
                AND good.created_at >= now() - interval '7 days'
        """)
        eff = session.execute(eff_sql).fetchone()
        
        rate = 0
        if eff.total_bad > 0:
            rate = int(eff.improved / eff.total_bad * 100)
            
    return f"""⚙️ <b>System Optimization (7d)</b>

Status: <b>{status}</b>

📉 <b>Auto-Actions:</b>
{log_str}

📋 <b>Review Queue (Open):</b>
{queue_str}

🧠 <b>Adaptation Effectiveness:</b>
• Users with Complaints: {eff.total_bad}
• Improved after Complaint: {eff.improved}
• Effectiveness Rate: <b>{rate}%</b>
"""

def get_back_markup():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Menu", callback_data="opro:menu"))
    return m

def get_investor_snapshot(days=7):
    # SQL Queries
    with get_sync_db() as session:
        # 1. Total Users
        total_users = session.execute(text("SELECT count(*) FROM users")).scalar()
        
        # 2. Active Users (Union strategy)
        # DailyLogs (need join) + AIUsage + Feedback
        active_sql = text(f"""
            SELECT count(distinct user_id) FROM (
                -- Daily Logs (via users join)
                SELECT u.telegram_id as user_id 
                FROM daily_logs dl
                JOIN users u ON dl.user_id = u.id
                WHERE dl.date >= to_char(now() - interval '{days} days', 'YYYY-MM-DD')
                
                UNION
                
                -- AI Usage
                SELECT user_id FROM ai_usage_logs WHERE timestamp >= now() - interval '{days} days'
                
                UNION
                
                -- Feedback
                SELECT user_id FROM menu_feedback WHERE created_at >= now() - interval '{days} days'
                UNION
                SELECT user_id FROM workout_feedback WHERE created_at >= now() - interval '{days} days'
                UNION
                SELECT user_id FROM coach_feedback WHERE created_at >= now() - interval '{days} days'
            ) t
        """)
        active_users = session.execute(active_sql).scalar() or 0
        
        # 3. Engaged (Feedback only)
        engaged_sql = text(f"""
            SELECT count(distinct user_id) FROM (
                SELECT user_id FROM menu_feedback WHERE created_at >= now() - interval '{days} days'
                UNION
                SELECT user_id FROM workout_feedback WHERE created_at >= now() - interval '{days} days'
                UNION
                SELECT user_id FROM coach_feedback WHERE created_at >= now() - interval '{days} days'
            ) t
        """)
        engaged_users = session.execute(engaged_sql).scalar() or 0
        
        # 4. Adapted
        # Updated recently OR has non-default settings
        adapted_sql = text(f"""
            SELECT count(distinct user_id) FROM user_adaptation_state
            WHERE updated_at >= now() - interval '{days} days'
               OR menu_kcal_adjust_pct != 0
               OR workout_soft_mode = true
        """)
        adapted_users = session.execute(adapted_sql).scalar() or 0
        
        # 7. Top Coach Messages
        top_coach = session.execute(text("""
            SELECT coach_msg_key, category, COUNT(*) as cnt 
            FROM coach_feedback 
            WHERE reaction='love' AND created_at >= now() - interval '7 days' 
            GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 3
        """)).fetchall()
        
        # 8/9 Distributions
        menu_dist = session.execute(text("SELECT rating, COUNT(*) FROM menu_feedback WHERE created_at >= now() - interval '7 days' GROUP BY 1 ORDER BY 2 DESC")).fetchall()
        workout_dist = session.execute(text("SELECT rating, COUNT(*) FROM workout_feedback WHERE created_at >= now() - interval '7 days' GROUP BY 1 ORDER BY 2 DESC")).fetchall()

    # Calculations
    coverage = int((engaged_users / active_users * 100)) if active_users else 0
    adapt_rate = int((adapted_users / engaged_users * 100)) if engaged_users else 0
    
    # Format
    top_coach_str = "\n".join([f"• {r[0]} ({r[1]}): {r[2]} ❤️" for r in top_coach]) or "No data"
    
    def fmt_dist(rows):
        return ", ".join([f"{r[0]}: {r[1]}" for r in rows]) or "No data"

    return f"""📌 <b>Investor Snapshot (Last {days}d)</b>

👥 <b>Growth & Activity:</b>
• Total Users: <code>{total_users}</code>
• Active Users: <code>{active_users}</code>
• Engaged (gave feedback): <code>{engaged_users}</code>

📈 <b>Metrics:</b>
• Feedback Coverage: <b>{coverage}%</b> (of active)
• Adaptation Rate: <b>{adapt_rate}%</b> (of engaged)
• Adapted Users: <code>{adapted_users}</code>

❤️ <b>Top Coach Content:</b>
{top_coach_str}

📊 <b>Sentiment:</b>
• Menu: {fmt_dist(menu_dist)}
• Workout: {fmt_dist(workout_dist)}
"""

def get_feedback_adaptation_report():
    with get_sync_db() as session:
        # A) Menu Bad -> Adapted
        menu_sql = text("""
             SELECT
              COUNT(DISTINCT mf.user_id) AS complained,
              COUNT(DISTINCT uas.user_id) AS adapted
            FROM (
              SELECT user_id, created_at FROM menu_feedback 
              WHERE rating = 'bad' AND created_at >= now() - interval '7 days'
            ) mf
            JOIN user_adaptation_state uas ON uas.user_id = mf.user_id
            WHERE uas.updated_at >= mf.created_at
               OR uas.menu_kcal_adjust_pct < 0
        """)
        menu_res = session.execute(menu_sql).fetchone()
        
        # B) Workout Tired -> Soft Mode
        work_sql = text("""
             SELECT
              COUNT(DISTINCT wf.user_id) AS tired,
              COUNT(DISTINCT uas.user_id) AS adapted
            FROM (
              SELECT user_id, created_at FROM workout_feedback 
              WHERE rating = 'tired' AND created_at >= now() - interval '7 days'
            ) wf
            JOIN user_adaptation_state uas ON uas.user_id = wf.user_id
            WHERE uas.workout_soft_mode = true
        """)
        work_res = session.execute(work_sql).fetchone()
        
        # C) Top Categories by Love
        cat_sql = text("""
            SELECT category, COUNT(*) as cnt
            FROM coach_feedback
            WHERE reaction = 'love'
            GROUP BY 1 ORDER BY 2 DESC LIMIT 5
        """)
        cats = session.execute(cat_sql).fetchall()
        
    menu_pct = int(menu_res.adapted / menu_res.complained * 100) if menu_res.complained else 0
    work_pct = int(menu_res.adapted / menu_res.complained * 100) if menu_res.complained else 0 # Should use work_res
    work_pct = int(work_res.adapted / work_res.tired * 100) if work_res.tired else 0

    cat_str = "\n".join([f"• {r[0]}: {r[1]}" for r in cats]) or "No data"

    return f"""🧠 <b>Feedback & Adaptation (Validation)</b>

🥗 <b>Menu Loop (Bad -> Adjust):</b>
• Complained (7d): {menu_res.complained}
• Adapted: {menu_res.adapted} users
• Conversion: <b>{menu_pct}%</b>

🏋️ <b>Workout Loop (Tired -> Soft):</b>
• Tired (7d): {work_res.tired}
• Soft Mode Active: {work_res.adapted} users
• Conversion: <b>{work_pct}%</b>

💡 <b>Top Loved Categories:</b>
{cat_str}
"""

def get_ai_cost_report():
    with get_sync_db() as session:
        # Cost last 30d
        cost_sql = text("""
            SELECT 
                SUM(cost_usd) as total,
                SUM(CASE WHEN feature='menu' THEN cost_usd ELSE 0 END) as menu,
                SUM(CASE WHEN feature='workout' THEN cost_usd ELSE 0 END) as workout,
                SUM(CASE WHEN feature='chat' THEN cost_usd ELSE 0 END) as chat
            FROM ai_usage_logs
            WHERE timestamp >= now() - interval '30 days'
        """)
        res = session.execute(cost_sql).fetchone()
        
        total = res.total or 0.0
        
        # Active users 30d for avg
        active_users = session.execute(text("""
            SELECT count(distinct user_id) FROM ai_usage_logs WHERE timestamp >= now() - interval '30 days'
        """)).scalar() or 1
        
        avg_cost = total / active_users
        
    return f"""💸 <b>AI Cost & Savings (30d)</b>

💰 <b>Total Spend: ${total:.4f}</b>
• Menu: ${res.menu or 0:.4f}
• Workout: ${res.workout or 0:.4f}
• Chat/Other: ${res.chat or 0:.4f}

bust <b>Efficiency:</b>
• Active AI Users: {active_users}
• Avg Cost/User: <b>${avg_cost:.4f}</b>

<i>Note: Savings from DB assembly are implicit by cost reduction per user over time.</i>
"""

from backend.database import get_sync_db, init_db_sync
from backend.models import User, DailyLog, Plan, Transaction, Feedback, Order, ActivityLog, CalorieLog, WorkoutCache, MenuCache, AdminLog, MenuTemplate, UserMenuLink, WorkoutTemplate, UserWorkoutLink, Subscription, AIUsageLog, Exercise, CoachMessage, EventLog
from sqlalchemy import func, desc, and_, or_, case
from datetime import datetime, timedelta
import json

import logging
import traceback
from sqlalchemy import text

logger = logging.getLogger("Database")

class Database:
    def __init__(self):
        init_db_sync()
        self.run_migrations()

    def run_migrations(self):
        """
        Auto-fix schema issues without full Alembic setup.
        Safe for production as it checks existence before modification.
        """
        with get_sync_db() as session:
            # Group migrations to manage flow
            def col_exists(table, column):
                if 'sqlite' in session.bind.dialect.name:
                    # SQLite compatible check
                    cursor = session.execute(text(f"PRAGMA table_info({table})"))
                    columns = [row[1] for row in cursor.fetchall()]
                    return column in columns
                
                sql = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
                return session.execute(sql).fetchone() is not None

            def add_col(table, column, col_type, default=None):
                if not col_exists(table, column):
                    logger.info(f"MIGRATION: Adding {column} to {table} table...")
                    default_sql = f" DEFAULT {default}" if default is not None else ""
                    session.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}{default_sql}"))
                    session.commit()
                    return True
                return False

            try:
                # 1. Transactions table fixes
                add_col('transactions', 'transaction_id', 'VARCHAR')
                add_col('transactions', 'perform_time', 'TIMESTAMP')
                add_col('transactions', 'cancel_time', 'TIMESTAMP')
                add_col('transactions', 'reason', 'INTEGER')
                
                # Indexes for transactions
                session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_transaction_id ON transactions (transaction_id)"))
                session.commit()

                # 2. Daily Logs fixes
                add_col('daily_logs', 'reminder_sent', 'BOOLEAN', 'FALSE')

                # 2. Daily Logs fixes
                add_col('daily_logs', 'reminder_sent', 'BOOLEAN', 'FALSE')

                # 3. Exercise Video Fixes (Phase 2/3)
                add_col('exercise_videos', 'video_url', 'VARCHAR')
                add_col('exercises', 'video_url', 'VARCHAR')
                
                # 4. Users table fixes (Handled via Alembic)

                # add_col('users', 'language', 'VARCHAR', "'uz'")

                # 5. Correctis_onboarded for existing users who have data
                # Identify users who have core profile data but are stuck in False
                onboarded_backfill = session.query(User).filter(
                    (User.is_onboarded == False) | (User.is_onboarded == None),
                    (User.age.isnot(None)) | (User.height.isnot(None)) | (User.goal.isnot(None))
                ).update({"is_onboarded": True}, synchronize_session=False)
                if onboarded_backfill > 0:
                    logger.info(f"MIGRATION: Backfilled is_onboarded=True for {onboarded_backfill} users with existing data.")
                
                session.commit()
                logger.info("✅ Database migrations checked/applied.")
                
                # Ensure all tables exist
                from backend.database import engine
                from backend.models import Base
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Verified all tables exist.")
                
            except Exception as e:

                session.rollback()
                logger.error(f"CRITICAL MIGRATION ERROR: {e}\n{traceback.format_exc()}")

    def init_db(self):
        init_db_sync()

    def save_meal_log(self, user_id, name, calories, protein, carbs, fat, meal_type, date):
        with get_sync_db() as session:
            from backend.models import MealLog
            log = MealLog(
                user_id=user_id,
                name=name,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                meal_type=meal_type,
                date=date
            )

            # Check for duplicates (same user, name, cals, within last half hour if possible, OR just same day same meal type/name)
            # Simple check: if exact same meal logged in the last 15 mins
            from datetime import datetime, timedelta
            duplicate_window = datetime.now() - timedelta(minutes=15)
            
            # We need to query. 
            # Since 'date' is string YYYY-MM-DD, we can check if a record exists with same details created_at > window
            # But MealLog might not have created_at populated by default or we need to rely on it.
            # Let's check models.py first to see if created_at exists.
            # Assuming created_at exists (common practice). If not we add strict check on name/date/type.
            
            # Let's inspect MealLog model first to be safe.
            # For now, let's just query for exact same entry on same date and type and name.
            # If the user eats the same thing twice in a day, they might want to log it twice.
            # But "I ate it" button spam usually happens rapidly.
            # A 1-minute window check on creation time would be ideal.
            
            existing = session.query(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.name == name,
                MealLog.meal_type == meal_type,
                MealLog.date == date,
                MealLog.calories == calories
            ).order_by(MealLog.id.desc()).first()
            
            if existing:
                # Check created_at if available
                if hasattr(existing, 'created_at'):
                    # Handle naive vs aware
                    created_at = existing.created_at
                    # Allow log if > 5 minutes passed
                    if (datetime.now() - created_at).total_seconds() < 300:
                        return False # Duplicate prevented
                else:
                     # If no created_at, just simplistic check
                     pass 

            session.add(log)
            session.commit() # Actually commit here to save
            return True

    def get_meal_logs(self, user_id, date):
        with get_sync_db() as session:
            from backend.models import MealLog
            return session.query(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.date == date
            ).all()

    def save_exercise_log(self, user_id, name, duration, calories_burned, date):
        with get_sync_db() as session:
            from backend.models import ExerciseLog
            log = ExerciseLog(
                user_id=user_id,
                name=name,
                duration=duration,
                calories_burned=calories_burned,
                date=date
            )
            session.add(log)
            return True

    def get_exercise_logs(self, user_id, date):
        with get_sync_db() as session:
            from backend.models import ExerciseLog
            return session.query(ExerciseLog).filter(
                ExerciseLog.user_id == user_id,
                ExerciseLog.date == date
            ).all()

            try:
                # 4. Create coach_messages and event_logs table
                from sqlalchemy import text
                
                # Coach Messages
                check_sql = text("SELECT to_regclass('public.coach_messages')")
                result = session.execute(check_sql).scalar()
                if not result:
                     print("MIGRATION: Creating coach_messages...")
                     sql = """
                     CREATE TABLE IF NOT EXISTS coach_messages (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        message TEXT,
                        date VARCHAR,
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
                     );
                     CREATE INDEX IF NOT EXISTS ix_coach_messages_date ON coach_messages (date);
                     """
                     session.execute(text(sql))
                     session.commit()

                # Event Logs
                check_sql2 = text("SELECT to_regclass('public.event_logs')")
                result2 = session.execute(check_sql2).scalar()
                if not result2:
                     print("MIGRATION: Creating event_logs...")
                     sql2 = """
                     CREATE TABLE IF NOT EXISTS event_logs (
                        id BIGSERIAL PRIMARY KEY,
                        user_id BIGINT,
                        event_type VARCHAR,
                        metadata_json TEXT,
                        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
                     );
                     CREATE INDEX IF NOT EXISTS ix_event_logs_event_type ON event_logs (event_type);
                     CREATE INDEX IF NOT EXISTS ix_event_logs_user_id ON event_logs (user_id);
                     CREATE INDEX IF NOT EXISTS ix_event_logs_created_at ON event_logs (created_at);
                     """
                     session.execute(text(sql2))
                     session.commit()
                     
            except Exception as e:
                session.rollback()
                print(f"MIGRATION ERROR 4: {e}")

            try:
                # 5. Create Analytics Views for Metabase (Automation)
                # This allows "Drag & Drop" in Metabase without writing SQL
                from sqlalchemy import text
                
                # View: Daily Summary (DAU, Events)
                session.execute(text("""
                CREATE OR REPLACE VIEW view_analytics_daily AS
                SELECT 
                    date_trunc('day', created_at) as day,
                    COUNT(DISTINCT user_id) as dau,
                    COUNT(*) as total_events
                FROM event_logs
                GROUP BY 1
                """))
                
                # View: Funnel Stats
                session.execute(text("""
                CREATE OR REPLACE VIEW view_analytics_funnel AS
                SELECT 
                    date_trunc('day', created_at) as day,
                    COUNT(*) FILTER (WHERE event_type='menu_generated') as menu_generated,
                    COUNT(*) FILTER (WHERE event_type='shopping_list_opened') as shopping_opened,
                    COUNT(*) FILTER (WHERE event_type='workout_generated') as workout_generated
                FROM event_logs
                GROUP BY 1
                """))

                session.commit()
                # print("MIGRATION: Analytics views updated!")
                
            except Exception as e:
                session.rollback()
                print(f"MIGRATION ERROR 5 (Views): {e}")





    def delete_user_by_id(self, telegram_id):
        """
        Hard delete user and all related data.
        Returns: (success: bool, message: str)
        """
        with get_sync_db() as session:
            try:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    return False, "Foydalanuvchi topilmadi"

                user_id = user.id
                
                # 1. Delete dependent tables (Manual cleanup for safety)
                # Note: Some might cascade, but being explicit is safer for 'Hard Delete'
                
                # Logs & Activities
                session.query(DailyLog).filter(DailyLog.user_id == user_id).delete()
                session.query(ActivityLog).filter(ActivityLog.user_id == user_id).delete()
                session.query(CalorieLog).filter(CalorieLog.user_id == user_id).delete()
                session.query(AIUsageLog).filter(AIUsageLog.user_id == user_id).delete()
                
                # Content & Plans
                session.query(Plan).filter(Plan.user_id == user_id).delete()
                session.query(UserMenuLink).filter(UserMenuLink.user_id == user_id).delete()
                session.query(UserWorkoutLink).filter(UserWorkoutLink.user_id == user_id).delete()
                session.query(WorkoutCache).filter(WorkoutCache.user_id == user_id).delete()
                session.query(MenuCache).filter(MenuCache.user_id == user_id).delete()
                
                # Financial
                session.query(Transaction).filter(Transaction.user_id == user_id).delete()
                session.query(Order).filter(Order.user_id == user_id).delete()
                session.query(Subscription).filter(Subscription.user_id == user_id).delete()
                
                # Misc
                session.query(Feedback).filter(Feedback.user_id == user_id).delete()
                
                # 2. Update Referrals (Set referrer to NULL for users referred by this user)
                session.query(User).filter(User.referrer_id == user_id).update({User.referrer_id: None})
                
                # 3. Delete User
                session.delete(user)
                
                session.commit()
                return True, f"User {telegram_id} va barcha ma'lumotlari o'chirildi."
                
            except Exception as e:
                session.rollback()
                print(f"Delete User Error: {e}")
                return False, f"Xatolik: {e}"


    def check_tiered_limit(self, user_id, feature_type):
        """
        Check if user can use a feature based on their plan.
        feature_type: 'menu_gen', 'calorie', 'chat'
        Returns: (allowed: bool, message: str, limit_info: str)
        """
        with get_sync_db() as session:
            # CIRCULAR IMPORT FIX
            from core.entitlements import get_usage_status, PLAN_PRO, PLAN_PLUS, PLAN_FREE
            
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return False, "User not found", ""

            # DELEGATE TO ENTITLEMENTS
            # Map feature_type to entitlement key
            key_map = {
                'menu_gen': 'menu_generate',
                'workout_gen': 'workout_generate',
                'calorie': 'calorie_scan',
                'chat': 'ai_chat'
            }
            ent_key = key_map.get(feature_type)
            if not ent_key: return False, "Unknown feature", ""
            
            status = get_usage_status(user_id, ent_key)
            
            # Formulate message similar to legacy format
            if status['remaining'] is not None and status['remaining'] <= 0:
                 # Reconstruct message based on plan
                 upgrade_to = PLAN_PLUS if status['plan'] == PLAN_FREE else PLAN_PRO
                 lang = getattr(user, 'language', 'uz')
                 
                 limit_display = f"{status['used']}/{status['limit']}"
                 
                 if lang == 'ru':
                     msg = "🔒 Лимит исчерпан."
                 else:
                     msg = f"🔒 Limit tugadi. {upgrade_to.capitalize()} tarifiga o'ting."
                     
                 return False, msg, limit_display
                 
            limit_display = "∞" if status['limit'] is None else f"{status['used']}/{status['limit']}"
            return True, "OK", limit_display

    def increment_tiered_usage(self, user_id, feature_type):
        """
        Increment usage using core.entitlements system.
        Legacy bridge for bot handlers.
        """
        key_map = {
            'menu_gen': 'menu_generate',
            'workout_gen': 'workout_generate',
            'chat': 'ai_chat',
            'calorie': 'calorie_scan'
        }
        ent_key = key_map.get(feature_type)
        
        # If unknown key, assume passed key is valid feature_key (e.g. from new code)
        if not ent_key: 
             ent_key = feature_type

        # Fix for raw user_id vs pk
        # entitlements usually expects telegram_id because it calls db.get_user(user_id) which is telegram_id based typically.
        # Let's verify entitlements.consume_usage input.
        # It calls get_usage_status => get_user_plan => db.get_user(user_id) 
        # db.get_user works with telegram_id. 
        # So we should pass telegram_id here. 
        # BUT increment_tiered_usage historically might accept telegram_id (from bot). 
        # Yes, handlers act on message.from_user.id.
        
        try:
             # CIRCULAR IMPORT FIX
             from core.entitlements import consume_usage
             consume_usage(user_id, ent_key)
        except Exception as e:
             logger.error(f"Failed to increment usage via entitlements: {e}")
             # Fallback? No, entitlements is source of truth now.
             pass

    def set_user_plan(self, user_id, plan_type, days=30):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            user = session.query(User).filter(User.id == pk).first()
            if not user: return
            
            user.plan_type = plan_type
            user.is_premium = True 
            
            # Logic: If already premium, extend. Else start from now.
            now = datetime.now()
            if user.premium_until and user.premium_until > now:
                user.premium_until = user.premium_until + timedelta(days=days)
            else:
                user.premium_until = now + timedelta(days=days)
            
            session.commit()
            
    def gift_premium_to_all(self, days=7, plan_type="trial"):
        """
        Gifts premium to ALL users Atomically.
        - If already premium: extends by 'days'.
        - If free/expired: gives 'days' starting now and sets plan_type.
        """
        with get_sync_db() as session:
            now = datetime.now()
            
            # Atomic Bulk Update
            row_count = session.query(User).update({
                "premium_until": func.greatest(func.coalesce(User.premium_until, now), now) + timedelta(days=days),
                "is_premium": True,
                "plan_type": case(
                    # If currently valid premium and plan is set, keep it. Else set to new plan.
                    (and_(User.premium_until > now, User.plan_type != None), User.plan_type),
                    else_=plan_type
                )
            }, synchronize_session=False)
            
            session.commit()
            return row_count

    # Legacy Wrapper to support existing calls, but warning: deprecated
    def check_ai_gen_limit(self, user_id, type_key='menu'):
         key = 'menu_gen' if type_key == 'menu' else 'workout_gen'
         allowed, msg, _ = self.check_tiered_limit(user_id, key)
         return allowed, msg

    def increment_ai_usage(self, user_id, type_key='menu'):
        key = 'menu_gen' if type_key == 'menu' else 'workout_gen'
        self.increment_tiered_usage(user_id, key)

    def reset_user_ai_limits(self, user_id):
        """Resets AI usage counters for a specific user to 0."""
        with get_sync_db() as session:
            # Query by telegram_id to be safe, or internal ID if that's what we pass. 
            # Looking at admin.py, we pass 'target_id' which is telegram_id usually.
            # But wait, set_user_plan uses _get_user_pk with user_id.
            pk = self._get_user_pk(session, user_id)
            if not pk: return False
            
            session.query(User).filter(User.id == pk).update(
                {
                    "ai_menu_count": 0,
                    "ai_workout_count": 0
                },
                synchronize_session=False
            )
            session.commit()
            return True

    def update_user_points(self, user_id, delta):
        """Update YASHA points for a user (delta can be negative)"""
        try:
            with get_sync_db() as session:
                from backend.models import User
                user = session.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    current = user.yasha_points or 0
                    user.yasha_points = max(0, current + delta) # Prevent negative
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"update_user_points Error: {e}")
            return False

    def clear_all_workout_caches(self):
        """Deletes all entries from WorkoutCache, WorkoutTemplate, and UserWorkoutLink."""
        with get_sync_db() as session:
            try:
                # Delete logic: Links first (FK), then Templates
                d1 = session.query(UserWorkoutLink).delete()
                d2 = session.query(WorkoutTemplate).delete()
                d3 = session.query(WorkoutCache).delete() # Legacy
                
                session.commit()
                return d1 + d2 + d3
            except Exception as e:
                print(f"Error clearing workout tables: {e}")
                return 0

    def get_active_users_batch(self, offset=0, limit=100):
        """Fetch users in batches to avoid OOM"""
        with get_sync_db() as session:
            # We want only 'active' users ideally? Or just all? 
            # Existing get_active_users gets all ids. Let's replicate logic but paginated.
            users = session.query(User.telegram_id)\
                          .filter(User.active == True)\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
            return [u[0] for u in users]

    def reset_db(self):
        from backend.database import sync_engine, Base
        from sqlalchemy import text
        
        # Try to drop with CASCADE for Postgres
        try:
            with sync_engine.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                conn.commit()
            print("DEBUG: Schema reset via CASCADE")
        except Exception as e:
            print(f"DEBUG: CASCADE drop failed: {e}")
            Base.metadata.drop_all(bind=sync_engine)
            
        Base.metadata.create_all(bind=sync_engine)

    def _get_user_pk(self, session, telegram_id):
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        return user.id if user else None

    def log_activity(self, user_id, type, payload):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                log = ActivityLog(user_id=pk, type=type, payload=payload)
                session.add(log)

    def get_weight_history(self, user_id, limit=30):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return []
            
            logs = session.query(ActivityLog.ts, ActivityLog.payload)\
                .filter(ActivityLog.user_id == pk, ActivityLog.type == 'weight_update')\
                .order_by(ActivityLog.ts.asc())\
                .all()
            return logs

    def get_checkin_history(self, user_id, days=7):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return []
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            logs = session.query(DailyLog.date, DailyLog.workout_done)\
                .filter(DailyLog.user_id == pk, DailyLog.date >= start_date)\
                .order_by(DailyLog.date.asc())\
                .all()
            return logs

    def add_user(self, telegram_id, username, phone, referral_code=None, referrer_id=None):
        with get_sync_db() as session:
            if session.query(User).filter(User.telegram_id == telegram_id).first():
                return True # Already exists
                
            ref_code = referral_code if referral_code else f"r{telegram_id}"
            
            # Resolve referrer_id (telegram_id) to PK
            referrer_pk = None
            if referrer_id:
                referrer_pk = self._get_user_pk(session, referrer_id)
            
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                phone=phone,
                referral_code=ref_code,
                referrer_id=referrer_pk,
                active=True
            )
            session.add(new_user)
            return True

    def update_user_profile(self, user_id, **kwargs):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
            session.commit()

    def get_user(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                # Convert to dict for compatibility
                return {c.name: getattr(user, c.name) for c in user.__table__.columns}
            return None

    def get_active_users_with_settings(self):
        """Legacy method - kept for backward compatibility if needed, but risky for large DB."""
        with get_sync_db() as session:
            users = session.query(User.telegram_id, User.full_name, User.username, User.notification_settings)\
                          .filter(User.active == True)\
                          .all()
            return [(u.telegram_id, u.full_name, u.username, u.notification_settings) for u in users]

    def get_active_users_batch(self, limit=100, offset=0):
        """Fetch active users in batches to prevent OOM."""
        with get_sync_db() as session:
            # We strictly order by ID to ensure stable pagination
            users = session.query(User.telegram_id, User.full_name, User.username, User.notification_settings, User.streak_water, User.streak_workout, User.last_checkin)\
                          .filter(User.active == True)\
                          .order_by(User.id)\
                          .limit(limit)\
                          .offset(offset)\
                          .all()
            
            # Return enriched structure for Coach
            results = []
            for u in users:
                results.append({
                    "id": u.telegram_id,
                    "full_name": u.full_name,
                    "username": u.username,
                    "settings": u.notification_settings,
                    "streak_water": u.streak_water or 0,
                    "streak_workout": u.streak_workout or 0,
                    "last_checkin": u.last_checkin
                })
            return results

    def check_specific_reminder_sent(self, user_id, date_str, type):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return True
            
            # Use event_logs to track various types of reminders
            day_start = datetime.strptime(date_str, "%Y-%m-%d")
            day_end = day_start + timedelta(days=1)
            
            log = session.query(EventLog).filter(
                EventLog.user_id == pk,
                EventLog.event_type == f"reminder_{type}",
                EventLog.created_at >= day_start,
                EventLog.created_at < day_end
            ).first()
            return log is not None

    def mark_specific_reminder_sent(self, user_id, date_str, type):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            log = EventLog(
                user_id=pk,
                event_type=f"reminder_{type}",
                metadata_json=json.dumps({"date": date_str})
            )
            session.add(log)
            session.commit()

    def add_points(self, user_id, points):
        with get_sync_db() as session:
            # Atomic update
            session.query(User).filter(User.telegram_id == user_id).update(
                {
                    "points": User.points + points,
                    "yasha_points": User.yasha_points + points
                },
                synchronize_session=False
            )

    def add_elixir(self, user_id, amount):
        with get_sync_db() as session:
            session.query(User).filter(User.telegram_id == user_id).update(
                {"elixir": User.elixir + amount},
                synchronize_session=False
            )
            session.commit()

    def get_daily_log(self, user_id, date_str):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            if log:
                return {c.name: getattr(log, c.name) for c in log.__table__.columns}
            return None

    def update_daily_log(self, user_id, date_str, **kwargs):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            if not log:
                log = DailyLog(user_id=pk, date=date_str)
                session.add(log)
            
            for key, value in kwargs.items():
                if hasattr(log, key):
                    setattr(log, key, value)
            session.commit()

    def check_reminder_sent(self, user_id, date_str):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return True
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            return log.reminder_sent if log else False

    def mark_reminder_sent(self, user_id, date_str):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            if not log:
                log = DailyLog(user_id=pk, date=date_str, reminder_sent=True)
                session.add(log)
            else:
                log.reminder_sent = True
            session.commit()

    def get_referral_count(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return 0
            return session.query(User).filter(User.referrer_id == pk).count()

    def get_friends_leaderboard(self, user_id, limit=10):
        """Get leaderboard of friends (referrals) + self"""
        with get_sync_db() as session:
            me = session.query(User).filter(User.telegram_id == user_id).first()
            if not me: return []
            
            # Friends: People I referred OR Me
            friends = session.query(User.full_name, User.points)\
                .filter(or_(User.referrer_id == me.id, User.id == me.id))\
                .order_by(desc(User.points))\
                .limit(limit)\
                .all()
            
            return friends

    def redeem_points(self, user_id, cost, days):
        """Atomic redemption of points"""
        from backend.models import User
        # We need a fresh session for atomic update
        with get_sync_db() as session:
            try:
                # 1. Check User & Balance
                user = session.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    return False, "Foydalanuvchi topilmadi"
                    
                if (user.yasha_points or 0) < cost:
                     return False, f"Hisobingizda yetarli ball yo'q! (Sizda: {user.yasha_points})"
                
                # 2. Atomic Decrement
                # Update returns number of matched rows
                rows = session.query(User).filter(and_(User.telegram_id == user_id, User.yasha_points >= cost))\
                    .update({User.yasha_points: User.yasha_points - cost}, synchronize_session=False)
                
                if rows == 0:
                    session.rollback()
                    return False, "Hisobingizda yetarli ball yo'q yoki xatolik!"
                
                # 3. Grant Premium (Inside SAME transaction)
                # Logic copied from set_premium but using current session object would be ideal.
                # Since set_premium uses 'with get_sync_db()', calling it here would create a NESTED session (new transaction).
                # To be truly atomic, we must do it manually here on 'session'.
                
                now = datetime.now()
                # Reload user or use update logic directly
                # We need to update premium_until on the SAME user record or via query
                
                session.query(User).filter(User.telegram_id == user_id).update({
                    "premium_until": func.greatest(func.coalesce(User.premium_until, now), now) + timedelta(days=days),
                    "is_premium": True
                }, synchronize_session=False)
                
                # 4. Commit ALL changes
                session.commit()
                return True, "Muvaffaqiyatli"
                
            except Exception as e:
                session.rollback()
                print(f"Redeem Error: {e}")
                return False, "Tizim xatoligi yuz berdi."

    def set_premium(self, user_id, days):
        with get_sync_db() as session:
            # Atomic update using SQL functions
            # premium_until = GREATEST(premium_until, now()) + days
            now = datetime.now()
            
            # Note: func.greatest is standard SQL. 
            # We use coalesce to handle NULL (treat as now)
            # But GREATEST(NULL, now) returns NULL in some SQL? user.premium_until might be Null.
            # COALESCE(premium_until, now) 
            
            # Logic: If existing future, add to it. If past or null, add to now.
            # GREATEST(COALESCE(premium_until, now), now) + days
            
            session.query(User).filter(User.telegram_id == user_id).update({
                "premium_until": func.greatest(func.coalesce(User.premium_until, now), now) + timedelta(days=days),
                "is_premium": True
            }, synchronize_session=False)
            session.commit()

    def is_premium(self, user_id):
        from core.entitlements import get_user_plan, PLAN_FREE
        return get_user_plan(user_id) != PLAN_FREE

    def get_premium_status(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return {"active": False, "type": "none"}
            
            is_active = user.premium_until and user.premium_until > datetime.now()
            
            status_type = "none"
            if is_active:
                if user.auto_renew:
                    status_type = "subscription"
                elif user.trial_used and user.trial_start:
                    try:
                        start = datetime.fromisoformat(user.trial_start) if isinstance(user.trial_start, str) else user.trial_start
                        if datetime.now() < start + timedelta(days=6):
                            status_type = "trial"
                        else:
                            status_type = "paid_fixed"
                    except:
                        status_type = "paid_fixed"
                else:
                    status_type = "paid_fixed"
                    
            return {
                "active": is_active,
                "type": status_type,
                "until": user.premium_until.isoformat() if user.premium_until else None,
                "auto_renew": user.auto_renew
            }

    def remove_premium(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.is_premium = False
                user.premium_until = None

    def add_feedback(self, user_id, message):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                fb = Feedback(user_id=pk, message=message)
                session.add(fb)

    def create_order(self, order_id, user_id, days, amount, currency='UZS'):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                order = Order(
                    order_id=order_id, user_id=pk, days=days, 
                    amount=amount, currency=currency, status='pending'
                )
                session.add(order)

    def update_order_status(self, order_id, status):
        with get_sync_db() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if order:
                order.status = status

    def get_order(self, order_id):
        with get_sync_db() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if order:
                return {c.name: getattr(order, c.name) for c in order.__table__.columns}
            return None

    def get_all_users(self):
        with get_sync_db() as session:
            users = session.query(User.telegram_id, User.full_name).all()
            return users

    def get_active_users(self):
        with get_sync_db() as session:
            users = session.query(User.telegram_id, User.full_name, User.username).filter(User.active == True).all()
            return users

    def get_users_paginated(self, page=1, page_size=20):
        with get_sync_db() as session:
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = session.query(User).count()
            
            # Get paginated users
            # Order by ID desc (newest first)
            users = session.query(User).order_by(User.id.desc()).limit(page_size).offset(offset).all()
            
            # Convert to dicts for safety
            users_list = []
            for user in users:
                item_data = {"id": user.telegram_id, "telegram_id": user.telegram_id, "full_name": user.full_name, "username": user.username, "phone": user.phone, "goal": user.goal, "gender": user.gender, "age": user.age, "height": user.height, "weight": user.weight, "activity_level": user.activity_level, "plan_type": user.plan_type, "premium_until": user.premium_until, "created_at": user.created_at, "updated_at": user.updated_at}
                users_list.append(item_data)
                
            return users_list, total_count
    
    def get_premium_users_paginated(self, page=1, page_size=20):
        """Get users with active premium subscription"""
        with get_sync_db() as session:
            from datetime import datetime
            offset = (page - 1) * page_size
            
            # Get total count of premium users
            base_q = session.query(User).filter(User.plan_type == 'premium', User.premium_until > datetime.now(), User.is_onboarded == True)
            total_count = base_q.count()
            
            # Get paginated premium users
            users = base_q.order_by(User.id.desc()).limit(page_size).offset(offset).all()
            
            users_list = []
            for user in users:
                item_data = {"id": user.telegram_id, "telegram_id": user.telegram_id, "full_name": user.full_name, "username": user.username, "phone": user.phone, "goal": user.goal, "gender": user.gender, "age": user.age, "height": user.height, "weight": user.weight, "activity_level": user.activity_level, "plan_type": user.plan_type, "premium_until": user.premium_until, "created_at": user.created_at, "updated_at": user.updated_at}
                users_list.append(item_data)
                
            return users_list, total_count
    
    def get_vip_users_paginated(self, page=1, page_size=20):
        """Get VIP users (users with 1000+ points or top tier)"""
        with get_sync_db() as session:
            offset = (page - 1) * page_size
            
            from datetime import datetime
            # Get users with VIP plan and active status
            base_q = session.query(User).filter(User.plan_type == 'vip', User.premium_until > datetime.now(), User.is_onboarded == True)
            total_count = base_q.count()
            
            users = base_q.order_by(User.premium_until.desc()).limit(page_size).offset(offset).all()
            
            users_list = []
            for user in users:
                item_data = {"id": user.telegram_id, "telegram_id": user.telegram_id, "full_name": user.full_name, "username": user.username, "phone": user.phone, "goal": user.goal, "gender": user.gender, "age": user.age, "height": user.height, "weight": user.weight, "activity_level": user.activity_level, "plan_type": user.plan_type, "premium_until": user.premium_until, "created_at": user.created_at, "updated_at": user.updated_at}
                users_list.append(item_data)
                
            return users_list, total_count
    
    def get_free_users_paginated(self, page=1, page_size=20):
        """Get free users (no active premium)"""
        with get_sync_db() as session:
            from datetime import datetime
            offset = (page - 1) * page_size
            
            # Users with free plan or expired premium/trial
            base_q = session.query(User).filter(
                (User.is_onboarded == True),
                ((User.plan_type == 'free') | (User.premium_until == None) | (User.premium_until <= datetime.now()))
            )
            total_count = base_q.count()
            
            users = base_q.order_by(User.id.desc()).limit(page_size).offset(offset).all()
            
            users_list = []
            for user in users:
                item_data = {"id": user.telegram_id, "telegram_id": user.telegram_id, "full_name": user.full_name, "username": user.username, "phone": user.phone, "goal": user.goal, "gender": user.gender, "age": user.age, "height": user.height, "weight": user.weight, "activity_level": user.activity_level, "plan_type": user.plan_type, "premium_until": user.premium_until, "created_at": user.created_at, "updated_at": user.updated_at}
                users_list.append(item_data)
                
            return users_list, total_count
    
    def get_top_referrers(self, limit=10):
        """Get top referrers by referral count"""
        with get_sync_db() as session:
            from sqlalchemy import func
            
            # Count referrals by grouping users by referrer_id
            # Get users who have referred others
            referral_stats = session.query(
                User.referrer_id.label('referrer_id'),
                func.count(User.id).label('referral_count')
            ).filter(
                User.referrer_id != None
            ).group_by(
                User.referrer_id
            ).order_by(
                func.count(User.id).desc()
            ).limit(limit).all()
            
            users_list = []
            for stat in referral_stats:
                # Get the referrer user details
                referrer = session.query(User).filter(User.telegram_id == stat.referrer_id).first()
                if referrer:
                    users_list.append({
                        "id": referrer.id,
                        "telegram_id": referrer.telegram_id,
                        "full_name": referrer.full_name,
                        "username": referrer.username,
                        "phone": referrer.phone,
                        "goal": referrer.goal,
                        "gender": referrer.gender,
                        "age": referrer.age,
                        "height": referrer.height,
                        "weight": referrer.weight,
                        "activity_level": referrer.activity_level,
                        "premium_until": referrer.premium_until,
                        "referral_count": stat.referral_count
                    })
                
            return users_list
    
    def get_incomplete_users_paginated(self, page=1, page_size=20):
        """Get users who haven't completed onboarding (missing profile data)"""
        with get_sync_db() as session:
            offset = (page - 1) * page_size
            
            # Users missing key profile fields
            # Users who haven't finished onboarding flag
            base_q = session.query(User).filter(User.is_onboarded == False)
            total_count = base_q.count()
            
            users = base_q.order_by(User.id.desc()).limit(page_size).offset(offset).all()
            
            users_list = []
            for user in users:
                item_data = {"id": user.telegram_id, "telegram_id": user.telegram_id, "full_name": user.full_name, "username": user.username, "phone": user.phone, "goal": user.goal, "gender": user.gender, "age": user.age, "height": user.height, "weight": user.weight, "activity_level": user.activity_level, "plan_type": user.plan_type, "premium_until": user.premium_until, "created_at": user.created_at, "updated_at": user.updated_at}
                users_list.append(item_data)
                
            return users_list, total_count

    def get_users_by_segment(self, gender=None, goal=None, activity_level=None, age_min=None, age_max=None, is_premium=None, language=None, plan_type=None, is_onboarded=None, inactive_days=None):
        with get_sync_db() as session:
            query = session.query(User.telegram_id, User.full_name, User.username).filter(User.active == True)
            
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            if age_min is not None: query = query.filter(User.age >= age_min)
            if age_max is not None: query = query.filter(User.age <= age_max)
            if language: query = query.filter(User.language == language)
            if plan_type: query = query.filter(User.plan_type == plan_type)
            if is_onboarded is not None: query = query.filter(User.is_onboarded == is_onboarded)
            
            if inactive_days is not None:
                cutoff = datetime.now() - timedelta(days=inactive_days)
                query = query.filter(User.updated_at <= cutoff)
            
            if is_premium is not None:
                now = datetime.now()
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return query.all()

    def get_users_by_segment_batch(self, gender=None, goal=None, activity_level=None, is_premium=None, language=None, plan_type=None, is_onboarded=None, inactive_days=None, offset=0, limit=100):
        with get_sync_db() as session:
            query = session.query(User.telegram_id).filter(User.active == True)
            
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            if language: query = query.filter(User.language == language)
            if plan_type: query = query.filter(User.plan_type == plan_type)
            if is_onboarded is not None: query = query.filter(User.is_onboarded == is_onboarded)
            
            if inactive_days is not None:
                cutoff = datetime.now() - timedelta(days=inactive_days)
                query = query.filter(User.updated_at <= cutoff)
            
            if is_premium is not None:
                now = datetime.now()
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return [u.telegram_id for u in query.offset(offset).limit(limit).all()]

    def get_active_users_count(self):
        with get_sync_db() as session:
            return session.query(User).filter(User.active == True).count()

    def get_segment_users_count(self, gender=None, goal=None, activity_level=None, is_premium=None, language=None, plan_type=None, is_onboarded=None, inactive_days=None):
        with get_sync_db() as session:
            query = session.query(User).filter(User.active == True)
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            if language: query = query.filter(User.language == language)
            if plan_type: query = query.filter(User.plan_type == plan_type)
            if is_onboarded is not None: query = query.filter(User.is_onboarded == is_onboarded)
            
            if inactive_days is not None:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=inactive_days)
                query = query.filter(User.updated_at <= cutoff)
            
            if is_premium is not None:
                now = datetime.now()
                from sqlalchemy import or_
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return query.count()

    def get_top_users(self, limit=20):
        with get_sync_db() as session:
            users = session.query(User.full_name, User.points)\
                .order_by(User.points.desc())\
                .limit(limit).all()
            return users
            
    def get_top_referrals(self, limit=10):
        with get_sync_db() as session:
            # Group by referrer_id and count
            # referrer_id is a PK to User.id
            # We want to show the referrer's name
            
            # Subquery to count referrals
            stmt = session.query(
                User.referrer_id, func.count('*').label('count')
            ).filter(User.referrer_id != None).group_by(User.referrer_id).subquery()
            
            # Join with User to get name
            results = session.query(User.full_name, User.telegram_id, stmt.c.count)\
                .join(stmt, User.id == stmt.c.referrer_id)\
                .order_by(stmt.c.count.desc())\
                .limit(limit).all()
                
            return [{"name": r[0], "id": r[1], "count": r[2]} for r in results]

    def set_user_active(self, user_id, active=True):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.active = active
            
    def export_csv(self):
        with get_sync_db() as session:
            users = session.query(User).all()
            if not users: return ""
            
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            columns = [c.name for c in User.__table__.columns]
            writer.writerow(columns)
            
            for user in users:
                writer.writerow([getattr(user, c) for c in columns])
                
            return output.getvalue()

    def get_stats(self):
        with get_sync_db() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.active == True).count()
            
            gender_stats = dict(session.query(User.gender, func.count(User.id)).group_by(User.gender).all())
            goal_stats = dict(session.query(User.goal, func.count(User.id)).group_by(User.goal).all())
            activity_stats = dict(session.query(User.activity_level, func.count(User.id)).group_by(User.activity_level).all())
            
            # Detailed Plan Stats (Synchronized with get_user_stats_counts)
            now = datetime.now()
            
            # 1. Premium (Paid)
            premium = session.query(func.count(User.id)).filter(
                User.plan_type == 'premium', 
                User.premium_until > now, 
                User.is_onboarded == True
            ).scalar() or 0
            
            # 2. VIP
            vip = session.query(func.count(User.id)).filter(
                User.plan_type == 'vip', 
                User.premium_until > now, 
                User.is_onboarded == True
            ).scalar() or 0
            
            # 3. Trial
            trial = session.query(func.count(User.id)).filter(
                User.plan_type == 'trial', 
                User.premium_until > now, 
                User.is_onboarded == True
            ).scalar() or 0
            
            # 4. Incomplete
            incomplete = session.query(func.count(User.id)).filter(
                User.is_onboarded == False
            ).scalar() or 0
            
            # UTM Stats
            utm_stats = dict(session.query(User.utm_source, func.count(User.id)).group_by(User.utm_source).all())
            
            return {
                "total": total_users,
                "active": active_users,
                "gender": gender_stats,
                "goal": goal_stats,
                "activity": activity_stats,
                "premium": premium,
                "vip": vip,
                "trial": trial,
                "incomplete": incomplete,
                "utm": utm_stats
            }

    def get_users_inactive_for(self, days):
        """
        Get users who were LAST updated exactly 'days' ago.
        This relies on 'updated_at' column in users table.
        """
        from backend.models import User
        from sqlalchemy import func
        import datetime
        
        now = datetime.datetime.utcnow()
        # Create a window: e.g., 3 days ago 00:00 to 3 days ago 23:59? 
        # Or just updated_at < now - days?
        # Requirement: "One message per milestone".
        # So we need strict window: updated_at BETWEEN (Start of Day X days ago) AND (End of Day X days ago)
        
        target_date = now - datetime.timedelta(days=days)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        with get_sync_db() as session:
            # Note: This assumes 'updated_at' is updated on every action. 
            # If not, we might be sending messages to active users if logic is flawed.
            # But 'log_activity' middleware updates DB? No, log_activity logs to admin_events/daily_logs usually.
            # 'users' table updated_at might strictly be profile updates.
            # However, for MVP and Rule 3 (No DB rename), we use what we have.
            # If 'daily_logs' is the source of truth for activity, we should check that.
            
            # Better approach: Get users where MAX(daily_log.date) == target_date? Expensive.
            # Let's stick to 'users.updated_at' if reliable, or just assume 'updated_at' is touched on main interactions.
            # If not, this feature might be weak. 
            # Alternative: We add 'last_active' column? No, Rule 3 forbids DB changes unless additive.
            # We can add a column? "Only ADD new layers... No renaming". Adding column is OK.
            # But let's try to use existing indexes. `daily_logs` has `user_id, date`.
            
            # Correct approach: Find users who have NO log in the last X days, BUT had a log X+1 days ago?
            # That's complicated.
            
            # Simple approach: Users.updated_at. AND verify we update it.
            return session.query(User).filter(
                User.updated_at >= start_of_day,
                User.updated_at <= end_of_day
            ).all()

    def touch_user_activity(self, user_id):
        """Helper to update user.updated_at on activity"""
        from backend.models import User
        import datetime
        with get_sync_db() as session:
            session.query(User).filter(User.telegram_id == user_id).update(
                {"updated_at": datetime.datetime.utcnow()}
            )
            session.commit()    
    def check_calorie_limit(self, user_id):
        from core.entitlements import get_usage_status
        status = get_usage_status(user_id, 'calorie_scan')
        if status['remaining'] is not None and status['remaining'] <= 0:
            return False, "limit_reached"
        return True, "ok"

    def increment_calorie_usage(self, user_id):
        from core.entitlements import check_and_consume
        check_and_consume(user_id, 'calorie_scan')

    def log_calorie_check(self, user_id, total_kcal, json_data):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                log = CalorieLog(user_id=pk, total_kcal=total_kcal, json_data=json_data)
                session.add(log)

    def complete_onboarding(self, telegram_id, username, profile_data, referrer_id=None):
        with get_sync_db() as session:
            try:
                # 1. Create or Get User
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    ref_code = f"r{telegram_id}"
                    
                    # Resolve referrer
                    referrer_pk = None
                    if referrer_id:
                        ref_user = session.query(User).filter(User.telegram_id == referrer_id).first()
                        if ref_user:
                            referrer_pk = ref_user.id

                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                        referral_code=ref_code,
                        referrer_id=referrer_pk,
                        active=True,
                        created_at=datetime.utcnow(),
                        language=profile_data.get('language', 'uz')
                    )
                    session.add(user)
                    session.flush() # Ensure user is attached
                else:
                    # User exists (created by ensure_user_exists), but might check if referrer needs to be set
                    if referrer_id and not user.referrer_id:
                         ref_user = session.query(User).filter(User.telegram_id == referrer_id).first()
                         if ref_user and ref_user.id != user.id:
                             user.referrer_id = ref_user.id
                             # Ensure referral code is set if missing
                    
                    if not user.referral_code:
                        user.referral_code = f"r{telegram_id}"

                
                # 2. Update Profile Data
                for key, value in profile_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                # 3. Activate Trial (3 days)
                now = datetime.now()
                user.premium_until = now + timedelta(days=3)
                user.is_premium = True
                user.is_onboarded = True
                user.plan_type = 'trial'
                user.trial_start = now.isoformat()
                user.trial_used = 1
                
                # 4. Award Referral Points (Atomic Update)
                if user.referrer_id:
                    session.query(User).filter(User.id == user.referrer_id).update(
                        {
                            "points": func.coalesce(User.points, 0) + 1,
                            "yasha_points": func.coalesce(User.yasha_points, 0) + 1
                        },
                        synchronize_session=False
                    )
                
                session.commit()
                return True
            except Exception as e:
                print(f"DB Error in complete_onboarding: {e}")
                session.rollback()
                raise e

    def get_weekly_stats(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            # 1. Get User Streaks
            user = session.query(User).filter(User.id == pk).first()
            streaks = {
                "current": user.streak if user else 0,
                "best": user.best_streak if user else 0
            }
            
            # 2. Get Last 7 Days Logs
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            logs = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date >= start_date).all()
            
            if not logs:
                return {"has_data": False, "streaks": streaks}
                
            # 3. Aggregate Data
            stats = {
                "has_data": True,
                "days_tracked": len(logs),
                "water_days": sum(1 for log in logs if log.water_drank),
                "workouts": sum(1 for log in logs if log.workout_done),
                "avg_sleep": 0,
                "moods": {},
                "streaks": streaks
            }
            
            total_sleep = sum(log.sleep_hours for log in logs if log.sleep_hours)
            sleep_count = sum(1 for log in logs if log.sleep_hours > 0)
            if sleep_count > 0:
                stats["avg_sleep"] = round(total_sleep / sleep_count, 1)
                
            for log in logs:
                if log.mood:
                    stats["moods"][log.mood] = stats["moods"].get(log.mood, 0) + 1
                    
            return stats

            day_ago = now - datetime.timedelta(hours=24)
            
            # DAU (Distinct users in logs + active users updated)
            # Simplest DAU: Distinct users in admin_events in last 24h
            dau = session.query(func.count(func.distinct(AdminEvent.user_id))).filter(
                AdminEvent.created_at >= day_ago
            ).scalar()
            
            # Error Rate
            total = session.query(AdminEvent).filter(AdminEvent.created_at >= day_ago).count()
            errors = session.query(AdminEvent).filter(
                AdminEvent.created_at >= day_ago, 
                AdminEvent.success == False
            ).count()
            
            error_rate = 0
            if total > 0:
                error_rate = round((errors / total) * 100, 1)
                
            return {
                "error_rate_24h": error_rate,
                "errors_24h": errors,
                "total_events_24h": total,
                "dau": dau or 0
            }

    # --- Observability ---
    def log_admin_event(self, event_type, user_id=None, success=True, latency_ms=None, meta=None):
        """Structured logging to DB"""
        from backend.models import AdminEvent
        import json
        with get_sync_db() as session:
            try:
                meta_str = json.dumps(meta) if meta else None
                event = AdminEvent(
                    user_id=user_id,
                    event_type=event_type,
                    success=success,
                    latency_ms=latency_ms,
                    meta=meta_str
                )
                session.add(event)
                session.commit()
            except Exception as e:
                print(f"Failed to log event: {e}")

    # --- Feature Flags ---
    def get_feature_flag(self, key):
        """Get raw flag data"""
        from backend.models import FeatureFlag
        with get_sync_db() as session:
            flag = session.query(FeatureFlag).filter(FeatureFlag.key == key).first()
            if not flag: return None
            
            return {
                "key": flag.key,
                "enabled": flag.enabled,
                "rollout_percent": flag.rollout_percent,
                "allowlist": flag.allowlist,
                "denylist": flag.denylist
            }

    def get_all_feature_flags(self):
        """Get all flags for admin panel"""
        from backend.models import FeatureFlag
        with get_sync_db() as session:
            flags = session.query(FeatureFlag).all()
            return [
                {
                    "key": f.key,
                    "enabled": f.enabled,
                    "rollout_percent": f.rollout_percent
                } 
                for f in flags
            ]

    def set_feature_flag(self, key, enabled, rollout_percent=None, allowlist=None, denylist=None):
        """Create or Update flag"""
        from backend.models import FeatureFlag
        import json
        with get_sync_db() as session:
            flag = session.query(FeatureFlag).filter(FeatureFlag.key == key).first()
            if not flag:
                flag = FeatureFlag(key=key)
                session.add(flag)
            
            flag.enabled = enabled
            if rollout_percent is not None:
                flag.rollout_percent = rollout_percent
            if allowlist is not None:
                flag.allowlist = json.dumps(allowlist)
            if denylist is not None:
                flag.denylist = json.dumps(denylist)
            
            session.commit()

    def get_todays_points_breakdown(self, user_id):
        default_breakdown = {
            "water": 0,
            "steps": 0,
            "sleep": 0,
            "mood": 0,
            "total": 0
        }
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return default_breakdown
            
            today = datetime.now().strftime("%Y-%m-%d")
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == today).first()
            
            breakdown = default_breakdown.copy()
            
            if log:
                # Re-calculate points based on log data (since we don't store points per log item explicitly yet)
                # This is an approximation based on rules
                if log.water_drank or (log.water_ml and log.water_ml >= 2500):
                    breakdown["water"] = 1
                
                if log.steps and log.steps >= 10000:
                    breakdown["steps"] = (log.steps // 10000) * 5
                    
                if log.sleep_hours and log.sleep_hours >= 8:
                    breakdown["sleep"] = 2
                    
                if log.mood == 'good':
                    breakdown["mood"] = 1
                    
            breakdown["total"] = sum(breakdown.values())
            return breakdown



    def update_streak(self, user_id, type):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                if type == 'water':
                    user.streak_water = (user.streak_water or 0) + 1
                elif type == 'mood':
                    user.streak_mood = (user.streak_mood or 0) + 1
            session.commit()

    # --- Persistent Onboarding Methods ---
    def get_onboarding_state(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                return user.onboarding_state or 0
            return 0

    def set_onboarding_state(self, user_id, state):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.onboarding_state = int(state)
                session.commit()

    def get_onboarding_data(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user and user.onboarding_data:
                try:
                    return json.loads(user.onboarding_data)
                except:
                    return {}
            return {}

    def update_onboarding_data(self, user_id, key, value):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                data = {}
                if user.onboarding_data:
                    try:
                        data = json.loads(user.onboarding_data)
                    except:
                        pass
                data[key] = value
                user.onboarding_data = json.dumps(data)
                session.commit()

    def clear_onboarding_state(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.onboarding_state = 0
                user.onboarding_data = "{}"
                session.commit()

    def ensure_user_exists(self, user_id, username=None, language="uz"):
        """Ensures a user record exists for onboarding."""
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                user = User(telegram_id=user_id, username=username, active=True, language=language)
                session.add(user)
                session.commit()
                return True
            return False

    def get_user_language(self, user_id):
        """Get user language preference"""
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            return user.language if user else "uz"

    def set_user_language(self, user_id, language):
        """Set user language preference"""
        with get_sync_db() as session:
            try:
                user = session.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    user.language = language
                    session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                print(f"Set User Language Error: {e}")
                return False

    # --- Monthly Menu Logic ---

    def get_menu_template(self, profile_key):
        with get_sync_db() as session:
            template = session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()
            if template:
                return {
                    "id": template.id,
                    "menu_json": template.menu_json,
                    "shopping_list_json": template.shopping_list_json
                }
            return None

    def delete_menu_template(self, profile_key):
        from sqlalchemy import text
        try:
            with get_sync_db() as session:
                # 1. Find Template ID first
                res = session.execute(
                    text("SELECT id FROM menu_templates WHERE profile_key = :pk"),
                    {"pk": profile_key}
                ).fetchone()
                
                if res:
                    template_id = res[0]
                    # 2. Delete Manual Links (Manual Cascade)
                    session.execute(
                        text("DELETE FROM user_menu_links WHERE menu_template_id = :tid"),
                        {"tid": template_id}
                    )
                    
                    # 3. Delete Template
                    # 3. Delete Template
                    session.execute(
                        text("DELETE FROM menu_templates WHERE id = :tid"),
                        {"tid": template_id}
                    )
                    # session.commit() handled by context manager on return/exit
                    return True
                return False
        except Exception as e:
            print(f"Error deleting menu template: {e}")
            return False

    def update_menu_template_content(self, profile_key, menu_json, shopping_list_json):
        from backend.models import MenuTemplate
        try:
            with get_sync_db() as session:
                template = session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()
                if template:
                    template.menu_json = menu_json
                    template.shopping_list_json = shopping_list_json
                    # Update timestamp if you had updated_at column, but we don't.
                    session.commit()
                    return template.id
                return None
        except Exception as e:
            print(f"Error updating menu template: {e}")
            return None

    def create_menu_template(self, profile_key, menu_json, shopping_list_json):
        with get_sync_db() as session:
            template = MenuTemplate(
                profile_key=profile_key,
                menu_json=menu_json,
                shopping_list_json=shopping_list_json
            )
            session.add(template)
            session.commit()
            return template.id

    def get_user_menu_link(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).order_by(UserMenuLink.id.desc()).first()
            
            if link:
                menu = session.query(MenuTemplate).filter(MenuTemplate.id == link.menu_template_id).first()
                if not menu: return None
                
                return {
                    "id": link.id,
                    "menu_template_id": link.menu_template_id,
                    "current_day_index": link.current_day_index,
                    "start_date": link.start_date,
                    "menu_json": menu.menu_json,
                    "shopping_list_json": menu.shopping_list_json
                }
            return None

    def get_daily_habit_progress(self, user_id):
        """
        Calculate completed habits for today (Water, Workout, Steps, Sleep).
        Returns a tuple: (completed_count, total_count)
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        total_habits = 4 # Water, Workout, Steps, Calories/Sleep? Let's use 4: Water, Workout, Steps, Calories
        
        try:
            with get_sync_db() as session:
                pk = self._get_user_pk(session, user_id)
                if not pk: return (0, total_habits)
                
                log = session.query(DailyLog).filter(
                    DailyLog.user_id == pk,
                    DailyLog.date == today
                ).first()
                
                if not log:
                    return (0, total_habits)
                
                completed = 0
                if log.water_drank: completed += 1
                if log.workout_done: completed += 1
                if (log.steps or 0) >= 5000: completed += 1 # Basic goal
                if (log.calories_consumed or 0) > 0: completed += 1 # Basic tracking
                
                return (completed, total_habits)
        except Exception as e:
            print(f"Error getting habit progress: {e}")
            return (0, total_habits)

    def add_daily_calories(self, user_id, kcal):
        """Atomic addition of calories to today's log"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        from backend.models import DailyLog
        
        with get_sync_db() as session:
            try:
                pk = self._get_user_pk(session, user_id)
                if not pk: return 0
                
                log = session.query(DailyLog).filter(
                    DailyLog.user_id == pk, 
                    DailyLog.date == today
                ).first()
                
                new_total = 0
                if not log:
                    log = DailyLog(user_id=pk, date=today, calories_consumed=kcal)
                    session.add(log)
                    new_total = kcal
                else:
                    log.calories_consumed = (log.calories_consumed or 0) + kcal
                    new_total = log.calories_consumed
                    
                session.commit()
                return new_total
            except Exception as e:
                print(f"Error adding calories: {e}")
                return 0

    def update_single_meal(self, user_id, day_idx, meal_type, new_meal_data):
        """VIP Swap: Update a single meal in the JSON menu"""
        from backend.models import UserMenuLink
        import json
        
        with get_sync_db() as session:
             try:
                 pk = self._get_user_pk(session, user_id)
                 if not pk: return False
                 
                 link = session.query(UserMenuLink).filter(UserMenuLink.user_id == pk, UserMenuLink.is_active == True).first()
                 if not link or not link.template: return False
                 
                 # Access menu data through template
                 menu_data = json.loads(link.template.menu_json)
                 
                 # Handle both dict and list formats
                 if isinstance(menu_data, dict) and "menu" in menu_data:
                     menu_list = menu_data["menu"]
                 elif isinstance(menu_data, list):
                     menu_list = menu_data
                 else:
                     return False
                 
                 # Find day (day_idx is 1-indexed)
                 idx = day_idx - 1
                 if 0 <= idx < len(menu_list):
                     day_data = menu_list[idx]
                     meals_root = day_data.get('meals', day_data)
                     meals_root[meal_type] = new_meal_data
                     
                     # Update template content
                     if isinstance(menu_data, dict):
                         menu_data["menu"] = menu_list
                         link.template.menu_json = json.dumps(menu_data)
                     else:
                         link.template.menu_json = json.dumps(menu_list)
                     
                     session.commit()
                     return True
                 return False
                 
             except Exception as e:
                 print(f"Update Meal Error: {e}")
                 return False

    def create_user_menu_link(self, user_id, template_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            # Deactivate old links
            session.query(UserMenuLink).filter(UserMenuLink.user_id == pk).update({"is_active": False})
            
            link = UserMenuLink(
                user_id=pk,
                menu_template_id=template_id,
                current_day_index=1,
                is_active=True
            )
            session.add(link)
            # Award Elixir for tracking food (+10)
            self.add_elixir(user_id, 10)
            session.commit()

    def deactivate_all_user_menus(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return False
            session.query(UserMenuLink).filter(UserMenuLink.user_id == pk).update({"is_active": False})
            session.commit()
            return True

    def update_menu_day(self, user_id, new_day_index):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return 1
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).first()
            
            if link:
                # new_day_index = max(1, min(30, new_day_index))
                new_day_index = max(1, new_day_index) # Relaxed limit
                link.current_day_index = new_day_index
                session.commit()
                return new_day_index
            return 1


    # =========================================================
    # WORKOUT TEMPLATE METHODS (Mirrors Menu Template)
    # =========================================================

    def create_workout_template(self, profile_key, workout_json):
        from backend.models import WorkoutTemplate
        try:
            with get_sync_db() as session:
                # Check exist first to avoid UniqueViolation
                existing = session.query(WorkoutTemplate).filter(WorkoutTemplate.profile_key == profile_key).first()
                if existing:
                     existing.workout_json = workout_json
                     session.commit()
                     return existing.id
                
                new_template = WorkoutTemplate(
                    profile_key=profile_key,
                    workout_json=workout_json
                )
                session.add(new_template)
                session.commit()
                return new_template.id
        except Exception as e:
            print(f"Create Workout Template Error: {e}")
            # Fallback to update just in case of race condition
            return self.update_workout_template_content(profile_key, workout_json)

    def update_workout_template_content(self, profile_key, workout_json):
        from backend.models import WorkoutTemplate
        try:
            with get_sync_db() as session:
                template = session.query(WorkoutTemplate).filter(WorkoutTemplate.profile_key == profile_key).first()
                if template:
                    template.workout_json = workout_json
                    session.commit()
                    return template.id
                return None
        except Exception as e:
            print(f"Error updating workout template: {e}")
            return None

    def get_workout_template(self, profile_key):
        from backend.models import WorkoutTemplate
        try:
            with get_sync_db() as session:
                template = session.query(WorkoutTemplate).filter(WorkoutTemplate.profile_key == profile_key).first()
                if template:
                    return {
                        "id": template.id,
                        "profile_key": template.profile_key,
                        "workout_json": template.workout_json
                    }
                return None
        except Exception as e:
            print(f"Error getting workout template: {e}")
            return None

    def delete_workout_template(self, profile_key):
        from sqlalchemy import text
        try:
            with get_sync_db() as session:
                # 1. Find Template ID first
                res = session.execute(
                    text("SELECT id FROM workout_templates WHERE profile_key = :pk"),
                    {"pk": profile_key}
                ).fetchone()
                
                if res:
                    template_id = res[0]
                    # 2. Delete Manual Links (Manual Cascade)
                    session.execute(
                        text("DELETE FROM user_workout_links WHERE workout_template_id = :tid"),
                        {"tid": template_id}
                    )
                    # 3. Delete Template
                    session.execute(
                        text("DELETE FROM workout_templates WHERE id = :tid"),
                        {"tid": template_id}
                    )
                    return True
                return False
        except Exception as e:
            print(f"Error deleting workout template: {e}")
            return False

    def create_user_workout_link(self, user_id, workout_template_id):
        from backend.models import UserWorkoutLink
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            # Deactivate old links
            self.deactivate_all_user_workouts(user_id)
            
            new_link = UserWorkoutLink(
                user_id=pk,
                workout_template_id=workout_template_id,
                current_day_index=1,
                is_active=True
            )
            session.add(new_link)
            session.commit()
            return new_link.id

    def deactivate_all_user_workouts(self, user_id):
        from sqlalchemy import text
        try:
            with get_sync_db() as session:
                pk = self._get_user_pk(session, user_id)
                session.execute(
                    text("UPDATE user_workout_links SET is_active = false WHERE user_id = :uid"),
                    {"uid": pk}
                )
        except Exception as e:
            print(f"Error deactivating workout links: {e}")

    def get_user_workout_link(self, user_id):
        from backend.models import UserWorkoutLink, WorkoutTemplate
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            link = session.query(UserWorkoutLink).filter(
                UserWorkoutLink.user_id == pk,
                UserWorkoutLink.is_active == True
            ).order_by(UserWorkoutLink.id.desc()).first()
            
            if link:
                work = session.query(WorkoutTemplate).filter(WorkoutTemplate.id == link.workout_template_id).first()
                if not work: return None
                
                return {
                    "id": link.id,
                    "workout_template_id": link.workout_template_id,
                    "current_day_index": link.current_day_index,
                    "start_date": link.start_date,
                    "workout_json": work.workout_json
                }
            return None

    def update_workout_day(self, user_id, new_day_index):
        from sqlalchemy import text
        try:
            with get_sync_db() as session:
                pk = self._get_user_pk(session, user_id)
                # Update latest active link
                session.execute(
                    text("""
                        UPDATE user_workout_links 
                        SET current_day_index = :day 
                        WHERE user_id = :uid AND is_active = true
                    """),
                    {"day": new_day_index, "uid": pk}
                )
                return new_day_index
        except Exception as e:
            print(f"Error updating workout day: {e}")
            return 1

    def get_users_for_report(self, mod_days=7):
        """
        Get users who joined exactly X*mod_days ago.
        Uses native SQL for efficiency.
        """
        from backend.models import User
        from sqlalchemy import text
        try:
            with get_sync_db() as session:
                # PostgreSQL specific: Check if (current_date - created_at_date) % mod == 0
                # And created_at is not null
                # We use raw sql for date math
                query = text("""
                    SELECT telegram_id, full_name, created_at 
                    FROM users 
                    WHERE active = true 
                    AND created_at IS NOT NULL
                    AND (CURRENT_DATE - DATE(created_at)) > 0
                    AND (CURRENT_DATE - DATE(created_at)) % :mod = 0
                """)
                result = session.execute(query, {"mod": mod_days}).fetchall()
                # Convert to dict list
            return [{"telegram_id": r[0], "full_name": r[1], "created_at": r[2]} for r in result]
        except Exception as e:
            print(f"Error getting report users: {e}")
            return []
    
    def clear_all_workout_caches(self):
        """Delete all AI-generated workout plans"""
        try:
            with get_sync_db() as session:
                from backend.models import UserWorkoutLink, WorkoutTemplate
                # Delete links first (FK)
                links_count = session.query(UserWorkoutLink).count()
                session.query(UserWorkoutLink).delete()
                
                # Delete templates
                templates_count = session.query(WorkoutTemplate).count()
                session.query(WorkoutTemplate).delete()
                
                session.commit()
                return links_count + templates_count
        except Exception as e:
            print(f"ERROR: Failed to clear workouts: {e}")
            return 0
    
    def clear_all_meals(self):
        """Delete all AI-generated meals"""
        try:
            with get_sync_db() as session:
                from backend.models import UserMenuLink, MenuTemplate
                # Delete links first (FK)
                links_count = session.query(UserMenuLink).count()
                session.query(UserMenuLink).delete()
                
                # Delete templates
                templates_count = session.query(MenuTemplate).count()
                session.query(MenuTemplate).delete()
                
                session.commit() 
                return links_count + templates_count
        except Exception as e:
            print(f"ERROR: Failed to clear meals: {e}")
            return 0
    
    def clear_user_meals(self, user_id):
        """Delete all AI-generated meals for a specific user"""
        try:
            with get_sync_db() as session:
                from backend.models import UserMeal
                count = session.query(UserMeal).filter(UserMeal.user_id == user_id).count()
                session.query(UserMeal).filter(UserMeal.user_id == user_id).delete()
                session.commit()
                return count
        except Exception as e:
            print(f"ERROR: Failed to clear user meals: {e}")
            return 0
    
    def clear_all_daily_plans(self):
        """Delete all daily plans"""
        try:
            with get_sync_db() as session:
                from backend.models import DailyPlan
                count = session.query(DailyPlan).count()
                session.query(DailyPlan).delete()
                session.commit() # Added commit for delete operation
                return count
        except Exception as e:
            print(f"ERROR: Failed to clear daily plans: {e}")
            return 0

    def update_user_utm(self, user_id, source, medium, campaign):
        """Update UTM tracking params for a user"""
        from backend.models import User
        with get_sync_db() as session:
            try:
                session.query(User).filter(User.telegram_id == user_id).update({
                    "utm_source": source,
                    "utm_raw": f"{source}_{medium}_{campaign}", # aggregated raw
                    "utm_campaign": campaign
                }, synchronize_session=False)
                session.commit()
            except Exception as e:
                print(f"UTM Update Error: {e}")

    def log_ai_usage_db(self, user_id, feature, model_name, input_tok, output_tok, cost_usd):
        """Log granular AI usage to DB"""
        from backend.models import AIUsageLog
        with get_sync_db() as session:
            try:
                log = AIUsageLog(
                    user_id=user_id,
                    feature=feature,
                    model_name=model_name,
                    input_tokens=input_tok,
                    output_tokens=output_tok,
                    total_tokens=input_tok + output_tok,
                    cost_usd=cost_usd,
                    timestamp=datetime.utcnow()
                )
                session.add(log)
                session.commit()
            except Exception as e:
                print(f"Db Log Error: {e}")

    def get_ai_usage_summary(self, days=30):
        """Get usage stats for Admin Dashboard"""
        from backend.models import AIUsageLog
        from sqlalchemy import func
        with get_sync_db() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total Cost & Tokens
            totals = session.query(
                func.sum(AIUsageLog.cost_usd),
                func.sum(AIUsageLog.total_tokens),
                func.count(AIUsageLog.id)
            ).filter(AIUsageLog.timestamp >= start_date).first()
            
            total_cost = totals[0] or 0.0
            total_tokens = totals[1] or 0
            total_reqs = totals[2] or 0
            
            # By Feature
            by_feature = session.query(
                AIUsageLog.feature,
                func.sum(AIUsageLog.cost_usd),
                func.count(AIUsageLog.id)
            ).filter(AIUsageLog.timestamp >= start_date)\
             .group_by(AIUsageLog.feature).all()
             
            # Top Spenders
            top_users = session.query(
                AIUsageLog.user_id,
                func.sum(AIUsageLog.cost_usd).label('spent')
            ).filter(AIUsageLog.timestamp >= start_date)\
             .group_by(AIUsageLog.user_id)\
             .order_by(func.sum(AIUsageLog.cost_usd).desc())\
             .limit(5).all()

            return {
                "period_days": days,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_requests": total_reqs,
                "by_feature": [{"name": f[0], "cost": f[1], "count": f[2]} for f in by_feature],
                "top_users": [{"user_id": u[0], "spent": u[1]} for u in top_users]
            }

    def activate_trial(self, user_id, days=3):
        """Activate Free Trial for new user."""
        from datetime import datetime, timedelta
        from backend.models import User
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return False
            
            user = session.query(User).filter(User.id == pk).first()
            if not user: return False
            
            # Check if already used trial
            if user.trial_used > 0:
                print(f"User {user_id} already used trial.")
                return False
                
            user.plan_type = 'trial'
            user.premium_until = datetime.utcnow() + timedelta(days=days)
            user.trial_used = 1
            user.is_premium = True
            
            session.commit()
            print(f"Trial activated for {user_id} ({days} days)")
            return True

    def check_subscription_status(self, user_id):
        """Check if subscription/trial valid. Downgrade if expired. Returns (is_active, plan_type)."""
        from datetime import datetime
        from backend.models import User
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return (False, 'free')
            
            user = session.query(User).filter(User.id == pk).first()
            if not user: return (False, 'free')
            
            # If Free, just return
            if user.plan_type == 'free':
                return (True, 'free')
            
            # If no expiry date set, assume permanent (unless trial logic fails)
            if not user.premium_until:
                return (True, user.plan_type)
                
            # Check expiry
            if user.premium_until < datetime.utcnow():
                # EXPIRED -> Downgrade
                old_plan = user.plan_type
                user.plan_type = 'free'
                user.is_premium = False
                user.premium_until = None
                session.commit()
                
                print(f"Downgraded user {user_id} from {old_plan} to free")
                return (False, 'expired')
                
            # Valid
            return (True, user.plan_type)

    # === Exercise Content Management ===
    def add_exercise(self, name, video_url, category="General", difficulty="All"):
        with get_sync_db() as session:
            try:
                ex = Exercise(
                    name=name,
                    video_url=video_url,
                    category=category,
                    difficulty=difficulty
                )
                session.add(ex)
                session.commit()
                return True
            except Exception as e:
                print(f"Add Exercise Error: {e}")
                session.rollback()
                return False

    def delete_exercise(self, exercise_id):
        with get_sync_db() as session:
            try:
                session.query(Exercise).filter(Exercise.id == exercise_id).delete()
                session.commit()
                return True
            except:
                session.rollback()
                return False

    def get_all_exercises(self):
        with get_sync_db() as session:
            try:
                exercises = session.query(Exercise).order_by(Exercise.category, Exercise.name).all()
                return [
                    {
                        "id": e.id,
                        "name": e.name,
                        "video_url": e.video_url,
                        "category": e.category,
                        "difficulty": e.difficulty
                    }
                    for e in exercises
                ]
            except:
                return []

    # === Coach Zone Methods ===
    def add_coach_message(self, user_id, message, date_str):
        with get_sync_db() as session:
            try:
                pk = self._get_user_pk(session, user_id)
                msg = CoachMessage(
                    user_id=pk,
                    message=message,
                    date=date_str,
                    is_read=False
                )
                session.add(msg)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Add Coach Msg Error: {e}")
                return False

    def get_today_coach_message(self, user_id, date_str):
        with get_sync_db() as session:
            try:
                pk = self._get_user_pk(session, user_id)
                msg = session.query(CoachMessage).filter(
                    CoachMessage.user_id == pk,
                    CoachMessage.date == date_str
                ).first()
                if msg: return msg.message
                return None
            except: return None
            
    # === Analytics / Event Login ===
    def log_event(self, user_id, event_type, metadata=None):
        """
        Log business event for analytics.
        Metadata is optional dict.
        """
        import json
        from datetime import datetime
        with get_sync_db() as session:
            try:
                meta_str = json.dumps(metadata) if metadata else "{}"
                
                # user_id can be BigInteger (telegram_id) directly in this table
                # We don't necessarily enforce FK to 'users' table for raw logs 
                # to allow logging even if user sync is lagging or for anonymous tracking
                
                log = EventLog(
                    user_id=user_id,
                    event_type=event_type,
                    metadata_json=meta_str,
                    created_at=datetime.utcnow()
                )
                session.add(log)
                session.commit()
            except Exception as e:
                # Analytics should fail silently in production
                print(f"Log Event Error: {e}")
    def get_total_users_count(self):
        with get_sync_db() as session:
            return session.query(func.count(User.id)).scalar() or 0

    def mass_reset_to_trial(self, days=14):
        """
        Mass update: All users to trial, cancel all subscriptions.
        """
        with get_sync_db() as session:
            trial_end = datetime.utcnow() + timedelta(days=days)
            trial_start_str = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 1. Update all users
            user_count = session.query(User).update({
                User.plan_type: "trial",
                User.is_premium: True,
                User.premium_until: trial_end,
                User.trial_start: trial_start_str,
                User.trial_used: 1
            }, synchronize_session=False)
            
            # 2. Deactivate all active subscriptions
            sub_count = session.query(Subscription).filter(Subscription.is_active == True).update({
                Subscription.is_active: False
            }, synchronize_session=False)
            
            session.commit()
            return user_count, sub_count

    def get_user_stats_counts(self):
        """
        Calculates counts for different user categories.
        """
        with get_sync_db() as session:
            from datetime import datetime
            now = datetime.now()
            
            # All
            total = session.query(func.count(User.id)).scalar() or 0
            
            # Categories based on active plan_type (must be onboarded)
            premium = session.query(func.count(User.id)).filter(User.plan_type == 'premium', User.premium_until > now, User.is_onboarded == True).scalar() or 0
            vip = session.query(func.count(User.id)).filter(User.plan_type == 'vip', User.premium_until > now, User.is_onboarded == True).scalar() or 0
            trial = session.query(func.count(User.id)).filter(User.plan_type == 'trial', User.premium_until > now, User.is_onboarded == True).scalar() or 0
            
            # Free: Either explicitly free, or expired premium/trial (must be onboarded)
            free = session.query(func.count(User.id)).filter(
                (User.is_onboarded == True),
                ((User.plan_type == 'free') | (User.premium_until == None) | (User.premium_until <= now))
            ).scalar() or 0
            
            # Incomplete (not onboarded)
            incomplete = session.query(func.count(User.id)).filter(User.is_onboarded == False).scalar() or 0
            
            return {
                "total": total,
                "premium": premium,
                "vip": vip,
                "trial": trial,
                "free": free,
                "incomplete": incomplete
            }

    def get_trial_users_paginated(self, page=1, page_size=10):
        with get_sync_db() as session:
            try:
                from datetime import datetime
                now = datetime.now()
                base_query = session.query(User).filter(User.plan_type == 'trial', User.premium_until > now, User.is_onboarded == True)
                total = base_query.count()
                users = base_query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
                
                result = []
                for u in users:
                    result.append({
                        'id': u.telegram_id,
                        'telegram_id': u.telegram_id,
                        'full_name': u.full_name or "Noma'lum",
                        'username': u.username,
                        'phone': u.phone,
                        'plan_type': u.plan_type,
                        'is_premium': u.is_premium,
                        'premium_until': u.premium_until,
                        'age': u.age,
                        'height': u.height,
                        'weight': u.weight,
                        'goal': u.goal,
                        'gender': u.gender,
                        'activity_level': u.activity_level,
                        'created_at': u.created_at,
                        'updated_at': u.updated_at
                    })
                return result, total
            except Exception as e:
                print(f"DB Error in get_trial_users_paginated: {e}")
                return [], 0

    def get_exercise_video(self, name):
        """Finds a video by exact name or fuzzy match."""
        with get_sync_db() as session:
            from backend.models import ExerciseVideo
            # 1. Exact match
            video = session.query(ExerciseVideo).filter(func.lower(ExerciseVideo.name) == name.lower()).first()
            if video:
                return {"file_id": video.file_id, "name": video.name, "video_url": video.video_url}
            
            # 2. Fuzzy match (Postgres specific or simple like)
            # Simple ILIKE for partial match
            video = session.query(ExerciseVideo).filter(ExerciseVideo.name.ilike(f"%{name}%")).first()
            if video:
                return {"file_id": video.file_id, "name": video.name, "video_url": video.video_url}
            return None

    def save_exercise_video(self, name, file_id, ymove_id=None, video_url=None):
        with get_sync_db() as session:
            from backend.models import ExerciseVideo
            video = session.query(ExerciseVideo).filter(ExerciseVideo.name == name).first()
            if not video:
                video = ExerciseVideo(name=name, file_id=file_id, ymove_id=ymove_id, video_url=video_url)
                session.add(video)
            else:
                video.file_id = file_id
                video.ymove_id = ymove_id
                if video_url:
                    video.video_url = video_url
            session.commit()

    def save_exercise(self, name, video_url=None, category=None, difficulty=None, 
                     description=None, muscle_group=None, equipment=None, duration_sec=None):
        """Save or update exercise in database"""
        with get_sync_db() as session:
            from backend.models import Exercise
            
            exercise = session.query(Exercise).filter(Exercise.name == name).first()
            if not exercise:
                exercise = Exercise(
                    name=name,
                    video_url=video_url,
                    category=category,
                    difficulty=difficulty,
                    description=description,
                    muscle_group=muscle_group,
                    equipment=equipment,
                    duration_sec=duration_sec
                )
                session.add(exercise)
            else:
                # Update existing
                if video_url: exercise.video_url = video_url
                if category: exercise.category = category
                if difficulty: exercise.difficulty = difficulty
                if description: exercise.description = description
                if muscle_group: exercise.muscle_group = muscle_group
                if equipment: exercise.equipment = equipment
                if duration_sec: exercise.duration_sec = duration_sec
            
            session.commit()

db = Database()

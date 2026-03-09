from backend.database import get_sync_db, init_db_sync
from backend.models import User, DailyLog, Plan, Transaction, Feedback, Order, ActivityLog, CalorieLog, WorkoutCache, MenuCache, AdminLog, MenuTemplate, UserMenuLink, WorkoutTemplate, UserWorkoutLink
from sqlalchemy import func, desc, and_, or_, case
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self):
        init_db_sync()

    def init_db(self):
        init_db_sync()
        # self.check_schema() # Deprecated: Use Alembic

    # check_schema removed in favor of Alembic

    def check_tiered_limit(self, user_id, feature_type):
        """
        Check if user can use a feature based on their plan.
        feature_type: 'menu_gen', 'calorie', 'chat'
        Returns: (allowed: bool, message: str, limit_info: str)
        """
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return False, "User not found", ""

            # Lazy Expiration Check
            if user.premium_until and user.premium_until < datetime.now():
                if user.plan_type != 'free':
                    user.plan_type = 'free'
                    user.is_premium = False
                    session.commit() # Commit downgrade
            
            plan = user.plan_type or 'free'
            
            # 1. Menu Generation Limit
            if feature_type == 'menu_gen':
                current_month = datetime.now().strftime("%Y-%m")
                
                # Reset monthly
                if user.ai_last_reset_month != current_month:
                    user.ai_menu_count = 0
                    user.ai_workout_count = 0
                    user.ai_last_reset_month = current_month
                    session.commit()
                
                usage = user.ai_menu_count
                
                # Limits
                if plan == 'vip': limit = 4
                elif plan == 'premium': limit = 1 # 1 week only
                elif plan == 'trial': limit = 1
                else: limit = 0 # Free
                
                if usage >= limit:
                    msg = "⚠️ Sizning limitingiz tugadi."
                    if plan == 'premium':
                        msg += "\n\nPremium tarifida oyiga 1 marta AI menyu olish mumkin. Ko'proq imkoniyat uchun VIP ga o'ting."
                    elif plan == 'trial':
                         msg += "\n\nSinov davri uchun Menyular limiti (1 ta) tugadi. Davom etish uchun tarif tanlang."
                    elif plan == 'free':
                         msg = "🔒 Bu funksiya faqat Premium/VIP da mavjud."
                    return False, msg, f"{usage}/{limit}"
                    
                return True, "OK", f"{usage}/{limit}"

            # 2. Workout Generation Limit
            elif feature_type == 'workout_gen':
                usage = user.ai_workout_count
                
                # Limits (Same structure as menu)
                if plan == 'vip': limit = 4
                elif plan == 'premium': limit = 1
                elif plan == 'trial': limit = 1
                else: limit = 0
                
                if usage >= limit:
                    msg = "⚠️ Sizning limitingiz tugadi."
                    if plan == 'premium':
                        msg += "\n\nPremium tarifida oyiga 1 marta AI mashq rejasi olish mumkin."
                    elif plan == 'trial':
                         msg += "\n\nSinov davri uchun Mashqlar limiti (1 ta) tugadi."
                    elif plan == 'free':
                         msg = "🔒 Bu funksiya faqat Premium/VIP da mavjud."
                    return False, msg, f"{usage}/{limit}"

                return True, "OK", f"{usage}/{limit}"

            # 2. Calorie / Chat (Daily Limits)
            # 2. Daily Limits (Calorie & Chat) - Atomic Column Based
            elif feature_type in ['calorie', 'chat']:
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Default values
                daily_limit = 0
                if plan == 'vip': daily_limit = 9999
                elif plan == 'premium': daily_limit = 3
                elif plan == 'trial': daily_limit = 1
                else: daily_limit = 0
                
                current_usage = 0
                last_use = None
                
                if feature_type == 'chat':
                    current_usage = user.chat_daily_uses or 0
                    last_use = user.chat_last_use_date
                elif feature_type == 'calorie':
                    current_usage = user.calorie_daily_uses or 0
                    last_use = user.calorie_last_use_date
                
                # Reset if new day
                if last_use != today:
                    current_usage = 0
                
                if current_usage >= daily_limit:
                    if plan == 'free':
                         return False, "🔒 Bu funksiya faqat Premium/VIP da mavjud.", f"{current_usage}/{daily_limit}"
                    
                    msg = f"⚠️ Kunlik limit ({daily_limit} ta) tugadi.\n\n"
                    if plan == 'premium':
                        msg += "Ertaga qaytib keling yoki cheksiz ishlatish uchun VIP ga o'ting! 🚀"
                    elif plan == 'trial':
                         msg += "Sinov davrida kuniga 1 marta mumkin. To'liq imkoniyat uchun Premium oling."
                    return False, msg, f"{current_usage}/{daily_limit}"
                
                return True, "OK", f"{current_usage}/{daily_limit}"
                
            return False, "Unknown feature", ""

    def increment_tiered_usage(self, user_id, feature_type):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            user = session.query(User).filter(User.id == pk).first()
            if not user: return
            
            if feature_type == 'menu_gen':
                session.query(User).filter(User.id == pk).update(
                    {"ai_menu_count": User.ai_menu_count + 1},
                    synchronize_session=False
                )
            elif feature_type == 'workout_gen':
                session.query(User).filter(User.id == pk).update(
                    {"ai_workout_count": User.ai_workout_count + 1},
                    synchronize_session=False
                )
            
            elif feature_type == 'chat':
                today = datetime.now().strftime("%Y-%m-%d")
                # Atomic increment or reset
                session.query(User).filter(User.id == pk).update({
                    "chat_daily_uses": case(
                        (User.chat_last_use_date == today, User.chat_daily_uses + 1),
                        else_=1
                    ),
                    "chat_last_use_date": today
                }, synchronize_session=False)

            elif feature_type == 'calorie':
                today = datetime.now().strftime("%Y-%m-%d")
                session.query(User).filter(User.id == pk).update({
                    "calorie_daily_uses": case(
                        (User.calorie_last_use_date == today, User.calorie_daily_uses + 1),
                        else_=1
                    ),
                    "calorie_last_use_date": today
                }, synchronize_session=False)
            
            session.commit()

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
        Gifts premium to ALL users.
        - If already premium: extends by 'days'.
        - If free: gives 'days' starting now.
        """
        count = 0
        with get_sync_db() as session:
            users = session.query(User).all()
            now = datetime.now()
            
            for user in users:
                user.is_premium = True
                
                # Careful not to overwrite a paid plan with 'trial' identifier if user is already premium
                # But here we just want to give access. Let's keep existing plan_type if strictly premium,
                # or overwrite if it was None.
                if not user.plan_type:
                    user.plan_type = plan_type
                
                if user.premium_until and user.premium_until > now:
                    user.premium_until = user.premium_until + timedelta(days=days)
                else:
                    user.premium_until = now + timedelta(days=days)
                    user.plan_type = plan_type # Ensure they get marked as trial if they were expired
                
                count += 1
            
            session.commit()
        return count

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

    def get_user(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                # Convert to dict for compatibility
                return {c.name: getattr(user, c.name) for c in user.__table__.columns}
            return None

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
            # Check and update in one query to prevent race condition
            # UPDATE users SET yasha_points = yasha_points - cost WHERE telegram_id = :uid AND yasha_points >= :cost
            
            # Using SQLAlchemy expression
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, "Foydalanuvchi topilmadi"
                
            # Check balance first (optional optimization but strictly need atomic update)
            if (user.yasha_points or 0) < cost:
                 return False, f"Hisobingizda yetarli ball yo'q! (Sizda: {user.yasha_points})"
            
            # Atomic decrement
            # Update returns number of matched rows
            rows = session.query(User).filter(and_(User.telegram_id == user_id, User.yasha_points >= cost))\
                .update({User.yasha_points: User.yasha_points - cost}, synchronize_session=False)
            
            if rows == 0:
                session.rollback()
                return False, "Hisobingizda yetarli ball yo'q yoki xatolik!"
                
            # If successful, add premium
            self.add_premium(user_id, days, "subscription") # This creates its own session, checking overlap
            
            # Since transaction committed? No, add_premium commits. 
            # We should commit this decrement first.
            session.commit()
            
            return True, "Muvaffaqiyatli"

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
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user or not user.premium_until:
                return False
            return user.premium_until > datetime.now()

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
                users_list.append({
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "phone": user.phone,
                    "goal": user.goal,
                    "premium_until": user.premium_until
                })
                
            return users_list, total_count

    def get_users_by_segment(self, gender=None, goal=None, activity_level=None, age_min=None, age_max=None, is_premium=None):
        with get_sync_db() as session:
            query = session.query(User.telegram_id, User.full_name, User.username).filter(User.active == True)
            
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            if age_min is not None: query = query.filter(User.age >= age_min)
            if age_max is not None: query = query.filter(User.age <= age_max)
            
            if is_premium is not None:
                now = datetime.now()
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return query.all()

    def get_users_by_segment_batch(self, gender=None, goal=None, activity_level=None, is_premium=None, offset=0, limit=100):
        with get_sync_db() as session:
            query = session.query(User.telegram_id).filter(User.active == True)
            
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            
            if is_premium is not None:
                now = datetime.now()
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return [u.telegram_id for u in query.offset(offset).limit(limit).all()]

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
            
            premium_users = session.query(User).filter(User.premium_until > datetime.now()).count()
            
            return {
                "total": total_users,
                "active": active_users,
                "gender": gender_stats,
                "goal": goal_stats,
                "activity": activity_stats,
                "premium": premium_users
            }

    def check_calorie_limit(self, user_id):
        if self.is_premium(user_id):
            return True, "premium"
            
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return False, "user_not_found"
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if user.calorie_last_use_date != today:
                return True, "free_daily"
            
            uses = user.calorie_daily_uses or 0
            if uses < 3:
                return True, "free_daily"
                
            return False, "limit_reached"

    def increment_calorie_usage(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if user.calorie_last_use_date != today:
                user.calorie_last_use_date = today
                user.calorie_daily_uses = 1
            else:
                user.calorie_daily_uses = (user.calorie_daily_uses or 0) + 1

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
                        created_at=datetime.utcnow()
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
                user.plan_type = 'trial'
                user.trial_start = now.isoformat()
                user.trial_used = 1
                
                # 4. Award Referral Points
                if user.referrer_id:
                    referrer = session.query(User).filter(User.id == user.referrer_id).first()
                    if referrer:
                        referrer.points = (referrer.points or 0) + 1
                        referrer.yasha_points = (referrer.yasha_points or 0) + 1
                        
                return True
            except Exception as e:
                print(f"DB Error in complete_onboarding: {e}")
                raise e

    def get_weekly_stats(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            # 1. Get User Streaks
            user = session.query(User).filter(User.id == pk).first()
            streaks = {
                "water": user.streak_water or 0,
                "sleep": user.streak_sleep or 0,
                "mood": user.streak_mood or 0
            }
            
            # 2. Get Last 7 Days Logs
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            logs = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date >= start_date).all()
            
            if not logs:
                return {"has_data": False}
                
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

    def redeem_points(self, user_id, cost, reward_type, reward_value):
        with get_sync_db() as session:
            # Atomic check and deduct
            # Returns number of rows updated (1 if success, 0 if condition failed)
            rows = session.query(User).filter(
                User.telegram_id == user_id, 
                User.points >= cost
            ).update(
                {
                    "points": User.points - cost,
                    "yasha_points": User.yasha_points - cost
                }, 
                synchronize_session=False
            )
            
            if rows == 0:
                return False, "Ballar yetarli emas"
            
            # Fetch user to grant reward (points already deducted in DB, but session object might be stale if we used synchronize_session=False)
            # We need to refresh or just query again
            user = session.query(User).filter(User.telegram_id == user_id).first()
            
            # Grant Reward
            if reward_type == "premium_days":
                days = int(reward_value)
                now = datetime.now()
                current_until = user.premium_until
                
                if current_until and current_until > now:
                    new_until = current_until + timedelta(days=days)
                else:
                    new_until = now + timedelta(days=days)
                
                user.premium_until = new_until
                user.is_premium = True
                
            return True, "Muvaffaqiyatli"

    def update_streak(self, user_id, type):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                if type == 'water':
                    user.streak_water = (user.streak_water or 0) + 1
                elif type == 'mood':
                    user.streak_mood = (user.streak_mood or 0) + 1

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

    def clear_onboarding_state(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.onboarding_state = 0
                user.onboarding_data = "{}"

    def ensure_user_exists(self, user_id, username=None):
        """Ensures a user record exists for onboarding."""
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                user = User(telegram_id=user_id, username=username, active=True)
                session.add(user)
                return True
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
                new_template = WorkoutTemplate(
                    profile_key=profile_key,
                    workout_json=workout_json
                )
                session.add(new_template)
                session.commit()
                return new_template.id
        except Exception as e:
            # Handle unique constraint violation gracefully by trying update
            print(f"Update fallback for workout: {e}")
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

db = Database()


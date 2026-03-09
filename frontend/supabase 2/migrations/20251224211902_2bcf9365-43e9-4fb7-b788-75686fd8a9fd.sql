-- Do'stlar tizimi
CREATE TABLE public.friendships (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  friend_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, accepted, rejected
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, friend_id)
);

ALTER TABLE public.friendships ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their friendships" ON public.friendships
  FOR SELECT USING (true);

CREATE POLICY "Users can create friendships" ON public.friendships
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their friendships" ON public.friendships
  FOR UPDATE USING (true);

CREATE POLICY "Users can delete their friendships" ON public.friendships
  FOR DELETE USING (true);

-- Challenge'lar
CREATE TABLE public.challenges (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  creator_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  challenge_type TEXT NOT NULL, -- steps, water, workout, weight
  target_value NUMERIC NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view challenges" ON public.challenges
  FOR SELECT USING (true);

CREATE POLICY "Users can create challenges" ON public.challenges
  FOR INSERT WITH CHECK (true);

-- Challenge ishtirokchilari
CREATE TABLE public.challenge_participants (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  challenge_id UUID REFERENCES public.challenges(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  current_value NUMERIC DEFAULT 0,
  joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(challenge_id, user_id)
);

ALTER TABLE public.challenge_participants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view participants" ON public.challenge_participants
  FOR SELECT USING (true);

CREATE POLICY "Users can join challenges" ON public.challenge_participants
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their progress" ON public.challenge_participants
  FOR UPDATE USING (true);

-- Kaloriya va ovqatlar
CREATE TABLE public.meals (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  calories NUMERIC NOT NULL,
  protein NUMERIC DEFAULT 0,
  carbs NUMERIC DEFAULT 0,
  fat NUMERIC DEFAULT 0,
  meal_type TEXT NOT NULL, -- breakfast, lunch, dinner, snack
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their meals" ON public.meals
  FOR SELECT USING (true);

CREATE POLICY "Users can create meals" ON public.meals
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their meals" ON public.meals
  FOR UPDATE USING (true);

CREATE POLICY "Users can delete their meals" ON public.meals
  FOR DELETE USING (true);

-- Mashqlar kutubxonasi
CREATE TABLE public.workouts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL, -- cardio, strength, flexibility, hiit
  duration_minutes INTEGER NOT NULL,
  difficulty TEXT NOT NULL, -- beginner, intermediate, advanced
  video_url TEXT,
  thumbnail_url TEXT,
  calories_burn INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.workouts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view workouts" ON public.workouts
  FOR SELECT USING (true);

-- Foydalanuvchi mashq tarixi
CREATE TABLE public.workout_logs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  workout_id UUID REFERENCES public.workouts(id),
  duration_minutes INTEGER NOT NULL,
  calories_burned INTEGER DEFAULT 0,
  completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.workout_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their workout logs" ON public.workout_logs
  FOR SELECT USING (true);

CREATE POLICY "Users can create workout logs" ON public.workout_logs
  FOR INSERT WITH CHECK (true);

-- Kundalik topshiriqlar
CREATE TABLE public.daily_tasks (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  task_type TEXT NOT NULL, -- water, steps, workout, meditation, meal
  target_value NUMERIC,
  coins_reward INTEGER NOT NULL DEFAULT 10,
  xp_reward INTEGER NOT NULL DEFAULT 20,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.daily_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view daily tasks" ON public.daily_tasks
  FOR SELECT USING (true);

-- Foydalanuvchi topshiriq bajarilishi
CREATE TABLE public.user_task_completions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  task_id UUID REFERENCES public.daily_tasks(id),
  completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  UNIQUE(user_id, task_id, date)
);

ALTER TABLE public.user_task_completions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their completions" ON public.user_task_completions
  FOR SELECT USING (true);

CREATE POLICY "Users can complete tasks" ON public.user_task_completions
  FOR INSERT WITH CHECK (true);

-- Foydalanuvchi levellari va tangalari
CREATE TABLE public.user_stats (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  level INTEGER NOT NULL DEFAULT 1,
  xp INTEGER NOT NULL DEFAULT 0,
  coins INTEGER NOT NULL DEFAULT 0,
  total_workouts INTEGER DEFAULT 0,
  total_calories_burned INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.user_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view stats" ON public.user_stats
  FOR SELECT USING (true);

CREATE POLICY "Users can create their stats" ON public.user_stats
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their stats" ON public.user_stats
  FOR UPDATE USING (true);

-- Do'kon mahsulotlari
CREATE TABLE public.shop_items (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  item_type TEXT NOT NULL, -- avatar, badge, theme, boost
  price_coins INTEGER NOT NULL,
  image_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.shop_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view shop items" ON public.shop_items
  FOR SELECT USING (true);

-- Foydalanuvchi xaridlari
CREATE TABLE public.user_purchases (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  item_id UUID REFERENCES public.shop_items(id),
  purchased_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, item_id)
);

ALTER TABLE public.user_purchases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their purchases" ON public.user_purchases
  FOR SELECT USING (true);

CREATE POLICY "Users can make purchases" ON public.user_purchases
  FOR INSERT WITH CHECK (true);

-- Eslatmalar sozlamalari
CREATE TABLE public.notification_settings (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  water_reminders BOOLEAN DEFAULT true,
  water_interval_hours INTEGER DEFAULT 2,
  workout_reminders BOOLEAN DEFAULT true,
  workout_time TIME DEFAULT '09:00',
  sleep_reminders BOOLEAN DEFAULT true,
  sleep_time TIME DEFAULT '22:00',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.notification_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their settings" ON public.notification_settings
  FOR SELECT USING (true);

CREATE POLICY "Users can create their settings" ON public.notification_settings
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their settings" ON public.notification_settings
  FOR UPDATE USING (true);

-- Boshlang'ich mashqlarni qo'shish
INSERT INTO public.workouts (title, description, category, duration_minutes, difficulty, calories_burn) VALUES
('Ertalabki cho''zish', 'Kun boshlanishida tanani uyg''otish uchun yengil cho''zish mashqlari', 'flexibility', 10, 'beginner', 50),
('HIIT Cardio', 'Yuqori intensivlikdagi interval mashq - yog'' yoqish uchun', 'hiit', 20, 'intermediate', 250),
('Kuch mashqlari', 'Butun tana uchun kuch mashqlari', 'strength', 30, 'intermediate', 200),
('Yoga Asoslari', 'Boshlang''ichlar uchun yoga mashqlari', 'flexibility', 25, 'beginner', 100),
('Qorin presslari', 'Qorin mushaklari uchun maxsus mashqlar', 'strength', 15, 'beginner', 120),
('Yugurish tayyorgarligi', 'Yugurish oldidan isitish mashqlari', 'cardio', 10, 'beginner', 80);

-- Boshlang'ich kundalik topshiriqlar
INSERT INTO public.daily_tasks (title, description, task_type, target_value, coins_reward, xp_reward) VALUES
('2.5L suv ich', 'Kunlik suv maqsadingizga erishing', 'water', 2500, 15, 30),
('10,000 qadam', 'Bugun 10 ming qadam yuring', 'steps', 10000, 20, 40),
('Mashq qiling', 'Kamida bitta mashq bajaring', 'workout', 1, 25, 50),
('Meditatsiya', '5 daqiqa meditatsiya qiling', 'meditation', 5, 10, 20),
('Sog''lom ovqat', 'Uchta sog''lom ovqat yeng', 'meal', 3, 15, 30);

-- Boshlang'ich do'kon mahsulotlari
INSERT INTO public.shop_items (name, description, item_type, price_coins, is_active) VALUES
('Oltin ramka', 'Profilingiz uchun oltin ramka', 'avatar', 100, true),
('Qorong''u tema', 'Maxsus qorong''u dizayn', 'theme', 200, true),
('2x XP Boost', '24 soat davomida 2 barobar XP', 'boost', 150, true),
('Chempion nishoni', 'Maxsus chempion nishoni', 'badge', 300, true),
('Kumush ramka', 'Profilingiz uchun kumush ramka', 'avatar', 50, true);
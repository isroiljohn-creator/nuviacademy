-- Fix RLS policies for weight_logs table (user_id is text type)
DROP POLICY IF EXISTS "Users can view their own weight logs" ON public.weight_logs;
DROP POLICY IF EXISTS "Users can insert their own weight logs" ON public.weight_logs;
DROP POLICY IF EXISTS "Users can update their own weight logs" ON public.weight_logs;
DROP POLICY IF EXISTS "Users can delete their own weight logs" ON public.weight_logs;

CREATE POLICY "Users can view own weight logs"
ON public.weight_logs FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own weight logs"
ON public.weight_logs FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own weight logs"
ON public.weight_logs FOR UPDATE
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own weight logs"
ON public.weight_logs FOR DELETE
USING (auth.uid()::text = user_id);

-- Fix RLS policies for achievements table
DROP POLICY IF EXISTS "Users can view their achievements" ON public.achievements;
DROP POLICY IF EXISTS "Users can earn achievements" ON public.achievements;

CREATE POLICY "Users can view own achievements"
ON public.achievements FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own achievements"
ON public.achievements FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Fix RLS policies for chat_messages table
DROP POLICY IF EXISTS "Users can view their chat messages" ON public.chat_messages;
DROP POLICY IF EXISTS "Users can create chat messages" ON public.chat_messages;

CREATE POLICY "Users can view own chat messages"
ON public.chat_messages FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own chat messages"
ON public.chat_messages FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Fix RLS policies for friendships table
DROP POLICY IF EXISTS "Users can view their friendships" ON public.friendships;
DROP POLICY IF EXISTS "Users can create friendships" ON public.friendships;
DROP POLICY IF EXISTS "Users can update their friendships" ON public.friendships;
DROP POLICY IF EXISTS "Users can delete their friendships" ON public.friendships;

CREATE POLICY "Users can view own friendships"
ON public.friendships FOR SELECT
USING (auth.uid()::text = user_id OR auth.uid()::text = friend_id);

CREATE POLICY "Users can create friendships"
ON public.friendships FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own friendships"
ON public.friendships FOR UPDATE
USING (auth.uid()::text = user_id OR auth.uid()::text = friend_id);

CREATE POLICY "Users can delete own friendships"
ON public.friendships FOR DELETE
USING (auth.uid()::text = user_id);

-- Fix RLS policies for meals table
DROP POLICY IF EXISTS "Users can view their meals" ON public.meals;
DROP POLICY IF EXISTS "Users can create meals" ON public.meals;
DROP POLICY IF EXISTS "Users can update their meals" ON public.meals;
DROP POLICY IF EXISTS "Users can delete their meals" ON public.meals;

CREATE POLICY "Users can view own meals"
ON public.meals FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own meals"
ON public.meals FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own meals"
ON public.meals FOR UPDATE
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own meals"
ON public.meals FOR DELETE
USING (auth.uid()::text = user_id);

-- Fix RLS policies for workout_logs table
DROP POLICY IF EXISTS "Users can view their workout logs" ON public.workout_logs;
DROP POLICY IF EXISTS "Users can create workout logs" ON public.workout_logs;

CREATE POLICY "Users can view own workout logs"
ON public.workout_logs FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own workout logs"
ON public.workout_logs FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Fix RLS policies for user_task_completions table
DROP POLICY IF EXISTS "Users can view their completions" ON public.user_task_completions;
DROP POLICY IF EXISTS "Users can complete tasks" ON public.user_task_completions;

CREATE POLICY "Users can view own task completions"
ON public.user_task_completions FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own task completions"
ON public.user_task_completions FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Fix RLS policies for user_stats table
DROP POLICY IF EXISTS "Users can view stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users can create their stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users can update their stats" ON public.user_stats;

CREATE POLICY "Users can view own stats"
ON public.user_stats FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own stats"
ON public.user_stats FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own stats"
ON public.user_stats FOR UPDATE
USING (auth.uid()::text = user_id);

-- Fix RLS policies for user_purchases table
DROP POLICY IF EXISTS "Users can view their purchases" ON public.user_purchases;
DROP POLICY IF EXISTS "Users can make purchases" ON public.user_purchases;

CREATE POLICY "Users can view own purchases"
ON public.user_purchases FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own purchases"
ON public.user_purchases FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Fix RLS policies for notification_settings table
DROP POLICY IF EXISTS "Users can view their settings" ON public.notification_settings;
DROP POLICY IF EXISTS "Users can create their settings" ON public.notification_settings;
DROP POLICY IF EXISTS "Users can update their settings" ON public.notification_settings;

CREATE POLICY "Users can view own notification settings"
ON public.notification_settings FOR SELECT
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own notification settings"
ON public.notification_settings FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own notification settings"
ON public.notification_settings FOR UPDATE
USING (auth.uid()::text = user_id);

-- Fix RLS policies for challenge_participants table
DROP POLICY IF EXISTS "Anyone can view participants" ON public.challenge_participants;
DROP POLICY IF EXISTS "Users can join challenges" ON public.challenge_participants;
DROP POLICY IF EXISTS "Users can update their progress" ON public.challenge_participants;

CREATE POLICY "Anyone can view challenge participants"
ON public.challenge_participants FOR SELECT
USING (true);

CREATE POLICY "Users can join challenges"
ON public.challenge_participants FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own participation"
ON public.challenge_participants FOR UPDATE
USING (auth.uid()::text = user_id);
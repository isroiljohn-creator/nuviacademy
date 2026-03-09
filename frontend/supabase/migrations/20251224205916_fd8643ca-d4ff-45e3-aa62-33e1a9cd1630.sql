-- Vazn kuzatuv jadvali
CREATE TABLE public.weight_logs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  weight DECIMAL(5,2) NOT NULL,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  note TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.weight_logs ENABLE ROW LEVEL SECURITY;

-- RLS policies - user_id asosida
CREATE POLICY "Users can view their own weight logs" 
ON public.weight_logs FOR SELECT 
USING (true);

CREATE POLICY "Users can insert their own weight logs" 
ON public.weight_logs FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Users can update their own weight logs" 
ON public.weight_logs FOR UPDATE 
USING (true);

CREATE POLICY "Users can delete their own weight logs" 
ON public.weight_logs FOR DELETE 
USING (true);

-- Yutuqlar/badjelar jadvali
CREATE TABLE public.achievements (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  badge_id TEXT NOT NULL,
  earned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, badge_id)
);

ALTER TABLE public.achievements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their achievements" 
ON public.achievements FOR SELECT 
USING (true);

CREATE POLICY "Users can earn achievements" 
ON public.achievements FOR INSERT 
WITH CHECK (true);

-- Chat tarixi jadvali (AI murabbiy uchun)
CREATE TABLE public.chat_messages (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their chat messages" 
ON public.chat_messages FOR SELECT 
USING (true);

CREATE POLICY "Users can create chat messages" 
ON public.chat_messages FOR INSERT 
WITH CHECK (true);
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Dumbbell, Play, Video, Clock, Flame, ChevronRight } from 'lucide-react';
import { WorkoutCard } from '@/components/WorkoutCard';
import { Paywall } from '@/components/Paywall';
import { DaySelector } from '@/components/DaySelector';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

const getWeekDays = (t: (key: string) => string) => [
  t('day.mon'), t('day.tue'), t('day.wed'), t('day.thu'), t('day.fri'), t('day.sat'), t('day.sun')
];

const getFreeWorkouts = (t: (key: string) => string) => [
  {
    title: t('workout.homeBasic'),
    duration: '25 ' + t('common.minutes'),
    calories: 180,
    exercises: 8,
  },
  {
    title: t('workout.cardioStretching'),
    duration: '20 ' + t('common.minutes'),
    calories: 150,
    exercises: 6,
  },
  {
    title: t('workout.upperBody'),
    duration: '30 ' + t('common.minutes'),
    calories: 220,
    exercises: 10,
  },
];

const getVideoWorkouts = (t: (key: string) => string) => [
  {
    id: 1,
    title: t('workout.homeCardio'),
    duration: '15 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: false,
  },
  {
    id: 2,
    title: t('workout.abs'),
    duration: '12 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: true,
  },
  {
    id: 3,
    title: t('workout.fullBody'),
    duration: '25 ' + t('common.minutes'),
    thumbnail: null,
    isLocked: true,
  },
];

interface WorkoutScreenProps {
  onNavigate?: (tab: string) => void;
}

export const WorkoutScreen: React.FC<WorkoutScreenProps> = ({ onNavigate }) => {
  const { isPremium, todayLog, markWorkoutDone, getTodayWorkouts, selectedDate, setSelectedDate } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [showPaywall, setShowPaywall] = useState(false);

  // State for daily plan
  const [weeklyPlan, setWeeklyPlan] = useState<any>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);

  // Fetch plan on mount
  React.useEffect(() => {
    const fetchPlan = async () => {
      try {
        const response = await axios.get('/ai/workout');
        if (response.data && response.data.plan) {
          setWeeklyPlan(response.data.plan);
        }
      } catch (error) {
        console.error("Failed to fetch workout plan:", error);
      } finally {
        setLoadingPlan(false);
      }
    };
    fetchPlan();
  }, []);

  const calculateDateStr = (index: number) => {
    const d = new Date();
    d.setDate(d.getDate() + index);
    return d.toISOString().split('T')[0];
  };

  const selectedDateStr = calculateDateStr(selectedDate);
  const isSelectedToday = selectedDate === 0;

  // Get daily workouts from plan or fallback
  const getDailyWorkouts = () => {
    if (!weeklyPlan || typeof weeklyPlan !== 'object') return [];

    try {
      // Map selectedDate (0=Today) to actual day name
      const d = new Date();
      d.setDate(d.getDate() + selectedDate);
      const dayName = d.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase(); // monday, tuesday...

      const dayPlan = weeklyPlan[dayName];

      if (!dayPlan || !Array.isArray(dayPlan)) return [];

      // Transform to UI format
      return dayPlan.map((ex: any, i: number) => ({
        id: i,
        title: ex.name,
        duration: (ex.duration || '2 min') + '',
        calories: ex.calories || 50,
        videoUrl: ex.video_url, // Enriched from backend
        isLocked: false, // Daily plan is unlocked if user has access to plan
        exercises: 1
      }));
    } catch (e) {
      console.error("Error parsing daily workouts:", e);
      return [];
    }
  };

  const dailyWorkouts = getDailyWorkouts();
  const weekDays = getWeekDays(t);

  // Use daily workouts if available, else fallback to hardcoded for demo if plan is empty
  const displayWorkouts = dailyWorkouts.length > 0 ? dailyWorkouts : (loadingPlan ? [] : getFreeWorkouts(t));

  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return {
      day: weekDays[date.getDay() === 0 ? 6 : date.getDay() - 1],
      date: date.getDate(),
      isToday: i === 0,
    };
  });

  const handleDaySelect = (index: number) => {
    vibrate('light');
    if (index > 0 && !isPremium()) {
      setShowPaywall(true);
      return;
    }
    setSelectedDate(index);
  };

  // State for active video
  const [activeVideo, setActiveVideo] = useState<string | null>(null);

  const handleWorkoutClick = (workout: any) => {
    vibrate('medium');
    if (!isPremium() && selectedDate > 0) {
      setShowPaywall(true);
      return;
    }

    if (workout.videoUrl) {
      setActiveVideo(workout.videoUrl);
    } else {
      // Just mark done if no video
      if (selectedDate === 0) markWorkoutDone();
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
    exit: { opacity: 0, transition: { duration: 0.1 } }
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 220,
        damping: 25
      }
    },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Active Video Player Modal/Overlay */}
      <AnimatePresence>
        {activeVideo && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed inset-0 z-50 bg-black flex flex-col items-center justify-center p-4"
          >
            <div className="absolute top-4 right-4 z-10">
              <button onClick={() => setActiveVideo(null)} className="p-2 bg-white/20 rounded-full text-white">
                ✕
              </button>
            </div>
            <div className="w-full max-w-lg aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
              <video
                src={activeVideo}
                controls
                autoPlay
                className="w-full h-full"
                playsInline
              />
            </div>
            <p className="text-white mt-4 text-center text-sm opacity-80">{t('workout.playingVideo')}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-2xl font-display font-bold text-foreground">
            {t('workout.title')}
          </h1>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Dumbbell className="w-4 h-4" />
            <span>{t('menu.weekly')}</span>
          </div>
        </div>

        {/* Day selector */}
        <div className="mb-5">
          <DaySelector
            days={days}
            selectedDay={selectedDate}
            onDaySelect={handleDaySelect}
            isPremium={isPremium()}
          />
        </div>

        {/* Premium info */}
        {!isPremium() && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-primary/10 border border-primary/30 rounded-xl p-3 mb-4"
          >
            <p className="text-sm text-foreground">
              <Lock className="w-4 h-4 inline mr-1" />
              {t('workout.premiumInfo')}
            </p>
          </motion.div>
        )}

        {/* Workout Library CTA */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => onNavigate?.('workout-library')}
          className="w-full p-4 rounded-xl bg-card border border-border/50 flex items-center justify-between group active:scale-[0.98] transition-all"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
              <Dumbbell className="w-5 h-5" />
            </div>
            <div className="text-left">
              <p className="text-sm font-bold text-foreground">{t('explore.workouts')}</p>
              <p className="text-xs text-muted-foreground">{t('explore.workoutsDesc')}</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-muted-foreground" />
        </motion.button>
      </div>

      {/* Workouts */}
      <AnimatePresence mode="wait">
        <motion.div
          key={selectedDate}
          variants={containerVariants}
          initial="hidden"
          animate="show"
          exit="exit"
          className="px-4 space-y-3"
        >
          <motion.p variants={itemVariants} className="text-sm text-muted-foreground mb-2">
            {t('common.day')} {selectedDate + 1} - {selectedDate === 0 ? t('common.today') : days[selectedDate].day}
          </motion.p>

          {loadingPlan ? (
            <div className="text-center py-10 opacity-50">Yuklanmoqda...</div>
          ) : (
            displayWorkouts.map((workout: any, index: number) => (
              <motion.div key={index} variants={itemVariants}>
                <div
                  onClick={() => handleWorkoutClick(workout)}
                  className="bg-card border border-border/50 rounded-xl p-4 flex items-center justify-between active:scale-[0.99] transition-transform"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center text-2xl">
                      {workout.videoUrl ? '📺' : '💪'}
                    </div>
                    <div>
                      <h3 className="font-bold text-foreground">{workout.title}</h3>
                      <p className="text-xs text-muted-foreground">{workout.duration} • {workout.calories} kcal</p>
                    </div>
                  </div>
                  {workout.videoUrl && <Play className="w-5 h-5 text-primary" />}
                  {workout.isLocked && !isPremium() && <Lock className="w-4 h-4 text-muted-foreground" />}
                </div>
              </motion.div>
            ))
          )}

          {displayWorkouts.length === 0 && !loadingPlan && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              Bugun dam olish kuni! 😴
            </div>
          )}

          {/* Tips section */}
          <motion.div
            variants={itemVariants}
            className="mt-6 p-4 rounded-2xl bg-card border border-border/50"
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl">💡</div>
              <div>
                <h3 className="font-semibold text-foreground text-sm mb-1">{t('menu.tip')}</h3>
                <p className="text-sm text-muted-foreground">
                  {t('workout.warmupTip')}
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>

      <Paywall
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        feature={t('paywall.aiWorkout')}
      />
    </div>
  );
};
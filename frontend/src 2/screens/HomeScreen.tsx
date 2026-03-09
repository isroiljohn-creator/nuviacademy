import React from 'react';
import { motion } from 'framer-motion';
import { Droplets, Footprints, Moon, Flame, Trophy, Bot, ChevronRight, Sparkles, Target, Utensils, Dumbbell, Zap, Coins } from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import yashaLogo from '@/assets/yasha-logo.png';

interface HomeScreenProps {
  onNavigate?: (tab: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  const { profile, todayLog, points, streaks, planType, premiumUntil, getTodayCalories, getTodayWorkouts } = useUser();
  const { t } = useLanguage();

  const waterProgress = todayLog ? (todayLog.water_ml / 2500) * 100 : 0;
  const stepsProgress = todayLog ? (todayLog.steps / 10000) * 100 : 0;
  const sleepProgress = todayLog ? (todayLog.sleep_hours / 8) * 100 : 0;

  // Get synced data from context
  const todayCalories = getTodayCalories();
  const todayWorkouts = getTodayWorkouts();
  const workoutDone = todayLog?.workout_done || todayWorkouts.length > 0;

  // Calculate daily calorie goal based on profile
  const calculateDailyGoal = () => {
    if (!profile) return 2000;

    let bmr: number;
    if (profile.gender === 'male') {
      bmr = 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age);
    } else {
      bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age);
    }

    const activityMultipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9,
    };

    let tdee = bmr * activityMultipliers[profile.activityLevel];

    if (profile.goal === 'weight_loss') tdee -= 500;
    else if (profile.goal === 'muscle_gain') tdee += 300;

    return Math.round(tdee);
  };

  const dailyGoal = calculateDailyGoal();
  const caloriesProgress = (todayCalories / dailyGoal) * 100;

  const getDaysRemaining = () => {
    if (!premiumUntil) return 0;
    const now = new Date();
    const diff = premiumUntil.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 260,
        damping: 20
      }
    },
  };

  const tapTransition = {
    whileTap: { scale: 0.98 },
    transition: { type: "spring", stiffness: 400, damping: 10 }
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-3 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <img src={yashaLogo} alt="YASHA" className="w-10 h-10" />
            <div>
              <h1 className="text-lg font-bold text-foreground">
                {t('home.greeting')}, {profile?.name || t('home.user')}!
              </h1>
              <p className="text-sm text-muted-foreground">
                {t('home.howAreYou')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Elixir */}
            <div className="flex items-center gap-1.5 bg-violet-500/10 px-2.5 py-1.5 rounded-full border border-violet-500/20 active:scale-95 transition-transform">
              <Zap className="w-4 h-4 text-violet-500 fill-violet-500/20" />
              <span className="text-sm font-bold text-violet-600">{useUser().elixir}</span>
            </div>

            {/* Tanga (Coins) */}
            <button
              onClick={() => onNavigate?.('achievements')}
              className="flex items-center gap-1.5 bg-amber-500/10 px-2.5 py-1.5 rounded-full border border-amber-500/20 active:scale-95 transition-transform"
            >
              <Coins className="w-4 h-4 text-amber-500 fill-amber-500/20" />
              <span className="text-sm font-bold text-amber-600">{points}</span>
            </button>
          </div>
        </div>

        {/* Trial/Premium Banner */}
        {(planType === 'trial' || planType === 'premium' || planType === 'vip' || planType === 'plus' || planType === 'pro') && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30 rounded-xl p-3.5"
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] text-primary font-semibold uppercase tracking-wider">
                  {planType === 'trial' ? t('home.trialPeriod') :
                    (planType === 'vip' || planType === 'pro' ? 'PRO' : 'PLUS')}
                </span>
                <p className="text-base font-bold text-foreground">
                  {getDaysRemaining()} {t('home.daysRemaining')}
                </p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
                <Flame className="w-5 h-5 text-primary" />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Today's Stats */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 mt-4"
      >
        <motion.h2 variants={itemVariants} className="text-sm font-semibold text-muted-foreground mb-2">
          {t('home.todayResults')}
        </motion.h2>

        <motion.button
          variants={itemVariants}
          whileTap={{ scale: 0.98 }}
          onClick={() => onNavigate?.('habits')}
          className="w-full"
        >
          <div className="grid grid-cols-2 gap-3">
            <motion.div variants={itemVariants}>
              <StatCard
                icon={Droplets}
                label={t('stats.water')}
                value={todayLog?.water_ml || 0}
                target="2500"
                unit="ml"
                progress={waterProgress}
                color="blue"
              />
            </motion.div>

            <motion.div variants={itemVariants}>
              <StatCard
                icon={Utensils}
                label={t('stats.calories')}
                value={todayCalories}
                target={dailyGoal.toString()}
                unit="kcal"
                progress={Math.min(caloriesProgress, 100)}
                color="orange"
              />
            </motion.div>

            <motion.div variants={itemVariants}>
              <StatCard
                icon={Moon}
                label={t('stats.sleep')}
                value={todayLog?.sleep_hours || 0}
                target="8"
                unit={t('common.hours')}
                progress={sleepProgress}
                color="purple"
              />
            </motion.div>

            <motion.div variants={itemVariants}>
              <StatCard
                icon={Dumbbell}
                label={t('stats.workout')}
                value={workoutDone ? `${t('stats.completed')} ✓` : t('stats.pending')}
                color={workoutDone ? 'primary' : 'primary'}
              />
            </motion.div>
          </div>
        </motion.button>

        {/* Streaks */}
        <motion.div variants={itemVariants} className="mt-3">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">{t('home.streaks')}</h3>
          <div className="grid grid-cols-4 gap-2">
            <div className="flex flex-col items-center p-2.5 rounded-xl bg-card border border-border/50">
              <Droplets className="w-4 h-4 text-blue-400 mb-1" />
              <p className="text-base font-bold text-foreground">{streaks.water}</p>
              <p className="text-[10px] text-muted-foreground">{t('stats.water').toLowerCase()}</p>
            </div>
            <div className="flex flex-col items-center p-2.5 rounded-xl bg-card border border-border/50">
              <Moon className="w-4 h-4 text-purple-400 mb-1" />
              <p className="text-base font-bold text-foreground">{streaks.sleep}</p>
              <p className="text-[10px] text-muted-foreground">{t('stats.sleep').toLowerCase()}</p>
            </div>
            <div className="flex flex-col items-center p-2.5 rounded-xl bg-card border border-border/50">
              <Dumbbell className="w-4 h-4 text-green-400 mb-1" />
              <p className="text-base font-bold text-foreground">{streaks.workout}</p>
              <p className="text-[10px] text-muted-foreground">{t('stats.workout').toLowerCase()}</p>
            </div>
            <div className="flex flex-col items-center p-2.5 rounded-xl bg-card border border-border/50">
              <Footprints className="w-4 h-4 text-orange-400 mb-1" />
              <p className="text-base font-bold text-foreground">{todayLog?.steps || 0}</p>
              <p className="text-[10px] text-muted-foreground">{t('stats.steps').toLowerCase()}</p>
            </div>
          </div>
        </motion.div>

        {/* AI Coach - Main CTA */}
        <motion.div variants={itemVariants} className="mt-4">
          <motion.button
            variants={itemVariants}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate?.('ai-coach')}
            className="w-full p-3.5 rounded-xl bg-gradient-to-r from-primary/25 to-primary/15 border border-primary/40 flex items-center justify-between transition-all active:scale-[0.98]"
          >
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-primary/25 flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-foreground">{t('home.aiCoach')}</p>
                <p className="text-xs text-muted-foreground">{t('home.personalAdvice')}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-primary" />
          </motion.button>
        </motion.div>

        {/* Daily Habits Button */}
        <motion.div variants={itemVariants} className="mt-2.5">
          <motion.button
            variants={itemVariants}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate?.('habits')}
            className="w-full p-3.5 rounded-xl bg-gradient-to-r from-emerald-500/20 to-teal-500/15 border border-emerald-500/30 flex items-center justify-between transition-all active:scale-[0.98]"
          >
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                <Target className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-foreground">{t('home.dailyHabits')}</p>
                <p className="text-xs text-muted-foreground">{t('home.waterSleepSteps')}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-emerald-400" />
          </motion.button>
        </motion.div>

        {/* Explore More Button */}
        <motion.div variants={itemVariants} className="mt-2.5 mb-4">
          <motion.button
            variants={itemVariants}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate?.('explore')}
            className="w-full p-3.5 rounded-xl bg-card border border-border/50 flex items-center justify-between transition-all active:scale-[0.98]"
          >
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-muted flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-muted-foreground" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-foreground">{t('home.exploreMore')}</p>
                <p className="text-xs text-muted-foreground">{t('home.friendsCompetition')}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          </motion.button>
        </motion.div>
      </motion.div>
    </div>
  );
};
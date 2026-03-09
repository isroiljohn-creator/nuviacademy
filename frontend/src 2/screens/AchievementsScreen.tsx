import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Droplets, Footprints, Moon, Flame, Star, Target, Award, Lock, ArrowLeft } from 'lucide-react';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

interface Badge {
  id: string;
  icon: React.ReactNode;
  titleKey: string;
  descKey: string;
  requirementKey: string;
  isUnlocked: boolean;
  progress: number;
  color: string;
}

interface AchievementsScreenProps {
  onBack?: () => void;
}

export const AchievementsScreen: React.FC<AchievementsScreenProps> = ({ onBack }) => {
  const { streaks, points, todayLog } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [earnedBadges, setEarnedBadges] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('yasha_badges');
    if (saved) {
      setEarnedBadges(JSON.parse(saved));
    }
  }, []);

  const badges: Badge[] = [
    {
      id: 'water_starter',
      icon: <Droplets className="w-6 h-6" />,
      titleKey: 'achievements.waterStarter',
      descKey: 'achievements.waterStarterDesc',
      requirementKey: 'achievements.1dayWater',
      isUnlocked: streaks.water >= 1,
      progress: Math.min(streaks.water, 1) * 100,
      color: 'blue'
    },
    {
      id: 'water_week',
      icon: <Droplets className="w-6 h-6" />,
      titleKey: 'achievements.waterMaster',
      descKey: 'achievements.waterMasterDesc',
      requirementKey: 'achievements.7dayStreak',
      isUnlocked: streaks.water >= 7,
      progress: (streaks.water / 7) * 100,
      color: 'blue'
    },
    {
      id: 'steps_starter',
      icon: <Footprints className="w-6 h-6" />,
      titleKey: 'achievements.stepCounter',
      descKey: 'achievements.stepCounterDesc',
      requirementKey: 'achievements.10kSteps',
      isUnlocked: (todayLog?.steps || 0) >= 10000,
      progress: ((todayLog?.steps || 0) / 10000) * 100,
      color: 'orange'
    },
    {
      id: 'sleep_master',
      icon: <Moon className="w-6 h-6" />,
      titleKey: 'achievements.sleepMaster',
      descKey: 'achievements.sleepMasterDesc',
      requirementKey: 'achievements.7dayStreak',
      isUnlocked: streaks.sleep >= 7,
      progress: (streaks.sleep / 7) * 100,
      color: 'purple'
    },
    {
      id: 'streak_fire',
      icon: <Flame className="w-6 h-6" />,
      titleKey: 'achievements.fireStreak',
      descKey: 'achievements.fireStreakDesc',
      requirementKey: 'achievements.14daysStreak',
      isUnlocked: Math.max(streaks.water, streaks.sleep, streaks.mood) >= 14,
      progress: (Math.max(streaks.water, streaks.sleep, streaks.mood) / 14) * 100,
      color: 'red'
    },
    {
      id: 'points_100',
      icon: <Star className="w-6 h-6" />,
      titleKey: 'achievements.starCollector',
      descKey: 'achievements.starCollectorDesc',
      requirementKey: 'achievements.100points',
      isUnlocked: points >= 100,
      progress: (points / 100) * 100,
      color: 'amber'
    },
    {
      id: 'points_500',
      icon: <Trophy className="w-6 h-6" />,
      titleKey: 'achievements.goldenCup',
      descKey: 'achievements.goldenCupDesc',
      requirementKey: 'achievements.500points',
      isUnlocked: points >= 500,
      progress: (points / 500) * 100,
      color: 'amber'
    },
    {
      id: 'all_habits',
      icon: <Target className="w-6 h-6" />,
      titleKey: 'achievements.perfectDay',
      descKey: 'achievements.perfectDayDesc',
      requirementKey: 'achievements.allGoals',
      isUnlocked: (todayLog?.water_ml || 0) >= 2500 && (todayLog?.steps || 0) >= 10000 && (todayLog?.sleep_hours || 0) >= 8,
      progress: ((((todayLog?.water_ml || 0) >= 2500 ? 1 : 0) + ((todayLog?.steps || 0) >= 10000 ? 1 : 0) + ((todayLog?.sleep_hours || 0) >= 8 ? 1 : 0)) / 3) * 100,
      color: 'primary'
    },
  ];

  const unlockedCount = badges.filter(b => b.isUnlocked).length;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    show: { opacity: 1, scale: 1 },
  };

  const getColorClasses = (color: string, isUnlocked: boolean) => {
    if (!isUnlocked) return 'bg-muted text-muted-foreground';
    const colors: Record<string, string> = {
      blue: 'bg-blue-500/20 text-blue-400',
      orange: 'bg-orange-500/20 text-orange-400',
      purple: 'bg-purple-500/20 text-purple-400',
      red: 'bg-red-500/20 text-red-400',
      amber: 'bg-amber-500/20 text-amber-400',
      primary: 'bg-primary/20 text-primary',
    };
    return colors[color] || 'bg-primary/20 text-primary';
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3">
          {onBack && (
            <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('achievements.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('achievements.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-4 mb-5">
        <div className="grid grid-cols-2 gap-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl bg-gradient-to-br from-primary/15 to-primary/5 border border-primary/30"
          >
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center mb-3">
              <Trophy className="w-5 h-5 text-primary" />
            </div>
            <p className="text-2xl font-bold text-foreground">{unlockedCount}/{badges.length}</p>
            <p className="text-sm text-muted-foreground">{t('achievements.badges')}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-4 rounded-2xl bg-card border border-border/50"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center mb-3">
              <Star className="w-5 h-5 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{points}</p>
            <p className="text-sm text-muted-foreground">{t('achievements.points')}</p>
          </motion.div>
        </div>
      </div>

      {/* Badges */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 grid grid-cols-2 gap-3"
      >
        {badges.map((badge) => (
          <motion.div
            key={badge.id}
            variants={itemVariants}
            whileTap={{ scale: 0.98 }}
            onClick={() => vibrate('light')}
            className={`p-4 rounded-2xl border transition-all ${
              badge.isUnlocked 
                ? 'bg-card border-border/50' 
                : 'bg-muted/30 border-border/30 opacity-60'
            }`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 ${getColorClasses(badge.color, badge.isUnlocked)}`}>
              {badge.isUnlocked ? badge.icon : <Lock className="w-5 h-5" />}
            </div>
            <h3 className="font-semibold text-foreground text-sm mb-1">{t(badge.titleKey)}</h3>
            <p className="text-xs text-muted-foreground mb-3">{t(badge.descKey)}</p>
            
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(badge.progress, 100)}%` }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className={`h-full rounded-full ${badge.isUnlocked ? 'bg-primary' : 'bg-muted-foreground/50'}`}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">{t(badge.requirementKey)}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
};

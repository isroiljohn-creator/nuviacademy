import React from 'react';
import { motion } from 'framer-motion';
import {
  Scale, Award, Brain, ChefHat, BarChart3, Users, Swords,
  CheckSquare, Dumbbell, ShoppingBag, Flame, ArrowLeft, ChevronRight
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface ExploreScreenProps {
  onNavigate?: (tab: string) => void;
  onBack?: () => void;
}

export const ExploreScreen: React.FC<ExploreScreenProps> = ({ onNavigate, onBack }) => {
  const { t } = useLanguage();

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  // Kategoriyalarga bo'lingan funksiyalar
  const trackingFeatures = [
    { id: 'weight', icon: Scale, labelKey: 'explore.weight', descKey: 'explore.weightDesc', color: 'blue' },
    { id: 'daily-tasks', icon: CheckSquare, labelKey: 'explore.tasks', descKey: 'explore.tasksDesc', color: 'amber' },
  ];

  const wellnessFeatures = [
    { id: 'meditation', icon: Brain, labelKey: 'explore.meditation', descKey: 'explore.meditationDesc', color: 'indigo' },
    { id: 'referrals', icon: Users, labelKey: 'explore.referrals', descKey: 'explore.referralsDesc', color: 'green' },
  ];

  const socialFeatures = [
    { id: 'friends', icon: Users, labelKey: 'explore.friends', descKey: 'explore.friendsDesc', color: 'cyan' },
    { id: 'challenges', icon: Swords, labelKey: 'explore.challenges', descKey: 'explore.challengesDesc', color: 'red' },
  ];

  const rewardFeatures = [
    { id: 'achievements', icon: Award, labelKey: 'explore.achievements', descKey: 'explore.achievementsDesc', color: 'amber' },
    { id: 'shop', icon: ShoppingBag, labelKey: 'explore.shop', descKey: 'explore.shopDesc', color: 'pink' },
  ];

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string }> = {
      blue: { bg: 'bg-blue-500/15', border: 'border-blue-500/30', text: 'text-blue-400' },
      orange: { bg: 'bg-orange-500/15', border: 'border-orange-500/30', text: 'text-orange-400' },
      amber: { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-400' },
      teal: { bg: 'bg-teal-500/15', border: 'border-teal-500/30', text: 'text-teal-400' },
      purple: { bg: 'bg-purple-500/15', border: 'border-purple-500/30', text: 'text-purple-400' },
      indigo: { bg: 'bg-indigo-500/15', border: 'border-indigo-500/30', text: 'text-indigo-400' },
      green: { bg: 'bg-green-500/15', border: 'border-green-500/30', text: 'text-green-400' },
      cyan: { bg: 'bg-cyan-500/15', border: 'border-cyan-500/30', text: 'text-cyan-400' },
      red: { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-400' },
      pink: { bg: 'bg-pink-500/15', border: 'border-pink-500/30', text: 'text-pink-400' },
    };
    return colors[color] || colors.blue;
  };

  const FeatureButton = ({ feature }: { feature: typeof trackingFeatures[0] }) => {
    const colors = getColorClasses(feature.color);
    return (
      <button
        onClick={() => onNavigate?.(feature.id)}
        className={`p-4 rounded-2xl ${colors.bg} border ${colors.border} text-center transition-all active:scale-95`}
      >
        <feature.icon className={`w-6 h-6 ${colors.text} mx-auto mb-2`} />
        <p className="text-sm font-semibold text-foreground">{t(feature.labelKey)}</p>
        <p className="text-xs text-muted-foreground">{t(feature.descKey)}</p>
      </button>
    );
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-5 pb-3 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2.5 rounded-full bg-card border border-border/50">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('explore.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('explore.subtitle')}</p>
          </div>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-6"
        >
          {/* Kuzatish va Tahlil */}
          <motion.div variants={itemVariants}>
            <h2 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
              📊 {t('explore.tracking')}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {trackingFeatures.map((feature) => (
                <FeatureButton key={feature.id} feature={feature} />
              ))}
            </div>
          </motion.div>

          {/* Sog'liq */}
          <motion.div variants={itemVariants}>
            <h2 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
              🧘 {t('explore.wellness')}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {wellnessFeatures.map((feature) => (
                <FeatureButton key={feature.id} feature={feature} />
              ))}
            </div>
          </motion.div>

          {/* Ijtimoiy */}
          <motion.div variants={itemVariants}>
            <h2 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
              👥 {t('explore.social')}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {socialFeatures.map((feature) => (
                <FeatureButton key={feature.id} feature={feature} />
              ))}
            </div>
          </motion.div>

          {/* Mukofotlar */}
          <motion.div variants={itemVariants}>
            <h2 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
              🏆 {t('explore.rewards')}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {rewardFeatures.map((feature) => (
                <FeatureButton key={feature.id} feature={feature} />
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Droplets, Footprints, Moon, Smile, Frown, Meh, Plus, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';

export const HabitsScreen: React.FC = () => {
  const { todayLog, addWater, updateTodayLog, isPremium } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [showStepsInput, setShowStepsInput] = useState(false);
  const [showSleepInput, setShowSleepInput] = useState(false);
  const [stepsInput, setStepsInput] = useState('');
  const [sleepInput, setSleepInput] = useState('');

  const moodOptions = [
    { value: 'bad', label: t('habits.moodBad'), icon: Frown, color: 'text-red-400' },
    { value: 'ok', label: t('habits.moodOk'), icon: Meh, color: 'text-yellow-400' },
    { value: 'good', label: t('habits.moodGood'), icon: Smile, color: 'text-green-400' },
  ];

  const supportiveMessages = [
    t('habits.badMoodMsg1'),
    t('habits.badMoodMsg2'),
    t('habits.badMoodMsg3'),
  ];

  const handleAddWater = () => {
    vibrate('success');
    addWater(250);
    toast.success(t('habits.waterAdded') + ' 💧');
  };

  const handleMoodSelect = (mood: 'bad' | 'ok' | 'good') => {
    vibrate('medium');
    updateTodayLog({ mood });
    
    if (mood === 'bad') {
      const message = supportiveMessages[Math.floor(Math.random() * supportiveMessages.length)];
      toast.info(message + ' 💚', { duration: 5000 });
    } else if (mood === 'good') {
      toast.success(t('habits.goodMoodMsg') + ' 🎉');
    }
  };

  const handleAddSteps = () => {
    const steps = parseInt(stepsInput) || 0;
    if (steps > 0) {
      vibrate('success');
      updateTodayLog({ steps: (todayLog?.steps || 0) + steps });
      setStepsInput('');
      setShowStepsInput(false);
      toast.success(`+${steps} ${t('habits.stepsAdded')} 🚶`);
    }
  };

  const handleSetSleep = () => {
    const hours = parseFloat(sleepInput) || 0;
    if (hours > 0) {
      vibrate('success');
      updateTodayLog({ sleep_hours: hours });
      setSleepInput('');
      setShowSleepInput(false);
      toast.success(`${hours} ${t('habits.sleepSaved')} 😴`);
    }
  };

  const handleStepsClick = () => {
    vibrate('light');
    setShowStepsInput(true);
  };

  const handleSleepClick = () => {
    vibrate('light');
    setShowSleepInput(true);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <h1 className="text-2xl font-display font-bold text-foreground mb-2">
          {t('habits.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('habits.subtitle')}
        </p>
      </div>

      {/* Habits */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-4"
      >
        {/* Water */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                (todayLog?.water_ml || 0) >= 2500 ? 'bg-success/20' : 'bg-blue-500/20'
              }`}>
                <Droplets className={`w-7 h-7 ${
                  (todayLog?.water_ml || 0) >= 2500 ? 'text-success' : 'text-blue-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">{t('habits.waterIntake')}</h3>
                <p className="text-sm text-muted-foreground">
                  {todayLog?.water_ml || 0} / 2,500 ml
                </p>
              </div>

              {(todayLog?.water_ml || 0) >= 2500 ? (
                <div className="w-12 h-12 rounded-xl bg-success/20 flex items-center justify-center">
                  <Check className="w-6 h-6 text-success" />
                </div>
              ) : (
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={handleAddWater}
                  className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-400 hover:bg-blue-500/30 transition-colors"
                >
                  <Plus className="w-6 h-6" />
                </motion.button>
              )}
            </div>
          </div>
        </motion.div>

        {/* Steps */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                (todayLog?.steps || 0) >= 10000 ? 'bg-success/20' : 'bg-orange-500/20'
              }`}>
                <Footprints className={`w-7 h-7 ${
                  (todayLog?.steps || 0) >= 10000 ? 'text-success' : 'text-orange-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">{t('habits.steps')}</h3>
                <p className="text-sm text-muted-foreground">
                  {todayLog?.steps || 0} / 10,000
                </p>
              </div>

              <AnimatePresence mode="wait">
                {showStepsInput ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="number"
                      value={stepsInput}
                      onChange={(e) => setStepsInput(e.target.value)}
                      placeholder={t('habits.steps')}
                      className="w-20 h-10 rounded-lg bg-muted text-center text-foreground border border-border"
                    />
                    <Button size="icon-sm" onClick={handleAddSteps}>
                      <Check className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ) : (todayLog?.steps || 0) >= 10000 ? (
                  <div className="w-12 h-12 rounded-xl bg-success/20 flex items-center justify-center">
                    <Check className="w-6 h-6 text-success" />
                  </div>
                ) : (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={handleStepsClick}
                    className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center text-orange-400 hover:bg-orange-500/30 transition-colors"
                  >
                    <Plus className="w-6 h-6" />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Sleep */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                (todayLog?.sleep_hours || 0) >= 8 ? 'bg-success/20' : 'bg-purple-500/20'
              }`}>
                <Moon className={`w-7 h-7 ${
                  (todayLog?.sleep_hours || 0) >= 8 ? 'text-success' : 'text-purple-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">{t('habits.sleep')}</h3>
                <p className="text-sm text-muted-foreground">
                  {todayLog?.sleep_hours || 0} / 8 {t('common.hours')}
                </p>
              </div>

              <AnimatePresence mode="wait">
                {showSleepInput ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="number"
                      step="0.5"
                      value={sleepInput}
                      onChange={(e) => setSleepInput(e.target.value)}
                      placeholder={t('common.hours')}
                      className="w-16 h-10 rounded-lg bg-muted text-center text-foreground border border-border"
                    />
                    <Button size="icon-sm" onClick={handleSetSleep}>
                      <Check className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ) : (todayLog?.sleep_hours || 0) >= 8 ? (
                  <div className="w-12 h-12 rounded-xl bg-success/20 flex items-center justify-center">
                    <Check className="w-6 h-6 text-success" />
                  </div>
                ) : (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={handleSleepClick}
                    className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400 hover:bg-purple-500/30 transition-colors"
                  >
                    <Plus className="w-6 h-6" />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Mood */}
        <motion.div variants={itemVariants}>
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <h3 className="font-semibold text-foreground mb-4">{t('habits.todayMood')}</h3>
            
            <div className="grid grid-cols-3 gap-3">
              {moodOptions.map((option) => {
                const Icon = option.icon;
                const isSelected = todayLog?.mood === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => handleMoodSelect(option.value as 'bad' | 'ok' | 'good')}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card hover:border-primary/30'
                    }`}
                  >
                    <Icon className={`w-8 h-8 mx-auto mb-2 ${option.color}`} />
                    <p className="text-sm font-medium text-foreground text-center">{option.label}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Daily tips */}
        <motion.div
          variants={itemVariants}
          className="mt-6 p-4 rounded-2xl bg-gradient-to-r from-primary/20 to-primary/10 border border-primary/30"
        >
          <h3 className="font-semibold text-foreground mb-2">💡 {t('habits.dailyTip')}</h3>
          <p className="text-sm text-muted-foreground">
            {t('habits.dailyTipText')}
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, CheckCircle, Coins, Star, Gift, Zap, Droplets, Footprints, Dumbbell, Moon, Utensils } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Progress } from '@/components/ui/progress';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';

interface DailyTasksScreenProps {
  onBack?: () => void;
}

export const DailyTasksScreen: React.FC<DailyTasksScreenProps> = ({ onBack }) => {
  const { toast } = useToast();
  const { todayLog, points, streaks, getTodayMeals, getTodayWorkouts } = useUser();
  const { t } = useLanguage();
  
  const todayMeals = getTodayMeals();
  const todayWorkouts = getTodayWorkouts();
  const workoutDone = todayLog?.workout_done || todayWorkouts.length > 0;

  const tasks = useMemo(() => [
    { id: '1', title: t('tasks.drinkWater'), description: t('tasks.drinkWaterDesc'), taskType: 'water', targetValue: 2500, currentValue: todayLog?.water_ml || 0, coinsReward: 15, xpReward: 30, completed: (todayLog?.water_ml || 0) >= 2500, icon: <Droplets className="w-5 h-5 text-blue-400" /> },
    { id: '2', title: t('tasks.walk10k'), description: t('tasks.walk10kDesc'), taskType: 'steps', targetValue: 10000, currentValue: todayLog?.steps || 0, coinsReward: 20, xpReward: 40, completed: (todayLog?.steps || 0) >= 10000, icon: <Footprints className="w-5 h-5 text-orange-400" /> },
    { id: '3', title: t('tasks.doWorkout'), description: t('tasks.doWorkoutDesc'), taskType: 'workout', targetValue: 1, currentValue: workoutDone ? 1 : 0, coinsReward: 25, xpReward: 50, completed: workoutDone, icon: <Dumbbell className="w-5 h-5 text-green-400" /> },
    { id: '4', title: t('tasks.sleep8h'), description: t('tasks.sleep8hDesc'), taskType: 'sleep', targetValue: 8, currentValue: todayLog?.sleep_hours || 0, coinsReward: 10, xpReward: 20, completed: (todayLog?.sleep_hours || 0) >= 8, icon: <Moon className="w-5 h-5 text-purple-400" /> },
    { id: '5', title: t('tasks.eat3meals'), description: t('tasks.eat3mealsDesc'), taskType: 'meal', targetValue: 3, currentValue: todayMeals.length, coinsReward: 15, xpReward: 30, completed: todayMeals.length >= 3, icon: <Utensils className="w-5 h-5 text-amber-400" /> },
  ], [todayLog, workoutDone, todayMeals.length, t]);

  const [claimedRewards, setClaimedRewards] = useState<string[]>(() => {
    const today = new Date().toISOString().split('T')[0];
    const saved = localStorage.getItem(`yasha_claimed_rewards_${today}`);
    return saved ? JSON.parse(saved) : [];
  });

  const userCoins = points;
  const userLevel = Math.floor(points / 100) + 1;
  const xpProgress = (points % 100);
  const completedTasks = tasks.filter(t => t.completed).length;
  const totalTasks = tasks.length;

  const handleClaimReward = (taskId: string) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || !task.completed || claimedRewards.includes(taskId)) return;
    const today = new Date().toISOString().split('T')[0];
    const newClaimed = [...claimedRewards, taskId];
    setClaimedRewards(newClaimed);
    localStorage.setItem(`yasha_claimed_rewards_${today}`, JSON.stringify(newClaimed));
    toast({ title: t('tasks.rewardReceived') + ' 🎉', description: `+${task.coinsReward} ${t('tasks.points')}, +${task.xpReward} XP` });
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50"><ArrowLeft className="w-5 h-5" /></button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-foreground">{t('tasks.title')}</h1>
            <p className="text-sm text-muted-foreground">{completedTasks}/{totalTasks} {t('tasks.completed')}</p>
          </div>
          <div className="flex items-center gap-2 bg-amber-500/20 px-3 py-1.5 rounded-full border border-amber-500/30">
            <Coins className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-bold text-amber-400">{userCoins}</span>
          </div>
        </div>

        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 mb-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-primary/20 flex items-center justify-center"><Star className="w-5 h-5 text-primary" /></div>
              <div>
                <p className="text-xs text-muted-foreground">{t('tasks.yourLevel')}</p>
                <p className="text-xl font-bold text-foreground">{t('tasks.level')} {userLevel}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-primary">{points} {t('tasks.points')}</p>
              <p className="text-xs text-muted-foreground">{t('tasks.next')}: {userLevel * 100}</p>
            </div>
          </div>
          <Progress value={xpProgress} className="h-2" />
        </motion.div>

        {completedTasks === totalTasks && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 mb-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center"><Gift className="w-5 h-5 text-amber-400" /></div>
                <div><p className="font-semibold text-foreground">{t('tasks.allCompleted')} 🎉</p><p className="text-sm text-muted-foreground">{t('tasks.greatJob')}</p></div>
              </div>
              <p className="font-bold text-amber-400">+50 {t('tasks.bonus')}</p>
            </div>
          </motion.div>
        )}

        <div className="space-y-3">
          <h2 className="text-base font-bold text-foreground">{t('tasks.todayTasks')}</h2>
          {tasks.map((task) => {
            const progress = (task.currentValue / task.targetValue) * 100;
            const isReady = task.completed && !claimedRewards.includes(task.id);
            const isClaimed = claimedRewards.includes(task.id);
            return (
              <motion.div key={task.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className={`p-4 rounded-xl border ${task.completed ? 'bg-success/10 border-success/30' : 'bg-card border-border/50'}`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start gap-3">
                    <div className={`p-2.5 rounded-xl ${task.completed ? 'bg-success/20' : 'bg-muted'}`}>{task.icon}</div>
                    <div>
                      <div className="flex items-center gap-2">{isClaimed && <CheckCircle className="w-4 h-4 text-success" />}<p className={`font-semibold ${task.completed ? 'text-success' : 'text-foreground'}`}>{task.title}</p></div>
                      <p className="text-sm text-muted-foreground mt-0.5">{task.description}</p>
                    </div>
                  </div>
                  <div className="text-right ml-3">
                    <div className="flex items-center gap-1 text-amber-400"><Coins className="w-3.5 h-3.5" /><span className="text-xs font-medium">+{task.coinsReward}</span></div>
                    <div className="flex items-center gap-1 text-primary"><Zap className="w-3.5 h-3.5" /><span className="text-xs font-medium">+{task.xpReward}</span></div>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mb-1"><span>{t('tasks.progress')}</span><span>{Math.min(task.currentValue, task.targetValue)}/{task.targetValue}</span></div>
                <div className="h-2 bg-muted rounded-full overflow-hidden mb-3"><motion.div className={`h-full rounded-full ${task.completed ? 'bg-success' : 'bg-primary'}`} initial={{ width: 0 }} animate={{ width: `${Math.min(progress, 100)}%` }} transition={{ duration: 0.5 }} /></div>
                {isReady && <Button size="sm" className="w-full" onClick={() => handleClaimReward(task.id)}><Gift className="w-4 h-4 mr-2" />{t('tasks.claimReward')}</Button>}
                {isClaimed && <div className="text-center text-sm text-success font-medium">✓ {t('tasks.rewardClaimed')}</div>}
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
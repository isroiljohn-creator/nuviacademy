import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Droplets, Footprints, Moon, Award, ArrowLeft } from 'lucide-react';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface ReportsScreenProps {
  onBack?: () => void;
}

export const ReportsScreen: React.FC<ReportsScreenProps> = ({ onBack }) => {
  const { todayLog, streaks, points } = useUser();
  const { t, language } = useLanguage();
  const [weeklyData, setWeeklyData] = useState<any[]>([]);

  useEffect(() => {
    const dayKeys = ['day.mon', 'day.tue', 'day.wed', 'day.thu', 'day.fri', 'day.sat', 'day.sun'];
    const today = new Date().getDay();
    const todayIndex = today === 0 ? 6 : today - 1;

    const data = dayKeys.map((dayKey, i) => {
      const isToday = i === todayIndex;
      
      // Faqat bugungi ma'lumotlarni ko'rsatamiz, o'tgan kunlar uchun 0
      return {
        day: t(dayKey),
        water: isToday ? (todayLog?.water_ml || 0) / 100 : 0,
        steps: isToday ? (todayLog?.steps || 0) / 1000 : 0,
        sleep: isToday ? (todayLog?.sleep_hours || 0) : 0,
      };
    });

    setWeeklyData(data);
  }, [todayLog, t, language]);

  const weeklyStats = {
    totalWater: weeklyData.reduce((sum, d) => sum + d.water * 100, 0),
    totalSteps: weeklyData.reduce((sum, d) => sum + d.steps * 1000, 0),
    avgSleep: weeklyData.filter(d => d.sleep > 0).length > 0 
      ? (weeklyData.reduce((sum, d) => sum + d.sleep, 0) / weeklyData.filter(d => d.sleep > 0).length).toFixed(1)
      : 0,
    completedDays: weeklyData.filter(d => d.water >= 25).length
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
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
            <h1 className="text-xl font-bold text-foreground">{t('reports.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('reports.subtitle')}</p>
          </div>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-4"
      >
        {/* Weekly summary cards */}
        <div className="grid grid-cols-2 gap-3">
          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-gradient-to-br from-blue-500/15 to-blue-500/5 border border-blue-500/30"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center mb-3">
              <Droplets className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{(weeklyStats.totalWater / 1000).toFixed(1)}L</p>
            <p className="text-sm text-muted-foreground">{t('reports.totalWater')}</p>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-gradient-to-br from-orange-500/15 to-orange-500/5 border border-orange-500/30"
          >
            <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center mb-3">
              <Footprints className="w-5 h-5 text-orange-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{(weeklyStats.totalSteps / 1000).toFixed(0)}K</p>
            <p className="text-sm text-muted-foreground">{t('reports.totalSteps')}</p>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-gradient-to-br from-purple-500/15 to-purple-500/5 border border-purple-500/30"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center mb-3">
              <Moon className="w-5 h-5 text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{weeklyStats.avgSleep}h</p>
            <p className="text-sm text-muted-foreground">{t('reports.avgSleep')}</p>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-gradient-to-br from-primary/15 to-primary/5 border border-primary/30"
          >
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center mb-3">
              <Award className="w-5 h-5 text-primary" />
            </div>
            <p className="text-2xl font-bold text-foreground">{weeklyStats.completedDays}/7</p>
            <p className="text-sm text-muted-foreground">{t('reports.goalDays')}</p>
          </motion.div>
        </div>

        {/* Water chart */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-2xl bg-card border border-border/50"
        >
          <div className="flex items-center gap-2 mb-4">
            <Droplets className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-foreground">{t('reports.waterChart')}</h3>
          </div>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyData}>
                <XAxis 
                  dataKey="day" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}
                  formatter={(value: number) => [`${value * 100}ml`, t('stats.water')]}
                />
                <Bar 
                  dataKey="water" 
                  fill="hsl(200, 80%, 50%)" 
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Steps chart */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-2xl bg-card border border-border/50"
        >
          <div className="flex items-center gap-2 mb-4">
            <Footprints className="w-5 h-5 text-orange-400" />
            <h3 className="font-semibold text-foreground">{t('reports.stepsChart')}</h3>
          </div>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyData}>
                <XAxis 
                  dataKey="day" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}
                  formatter={(value: number) => [`${(value * 1000).toLocaleString()}`, t('stats.steps')]}
                />
                <Bar 
                  dataKey="steps" 
                  fill="hsl(30, 80%, 50%)" 
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Motivation */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-2xl bg-gradient-to-r from-primary/15 to-primary/5 border border-primary/30"
        >
          <h3 className="font-semibold text-foreground mb-2">🎯 {t('reports.weeklyAnalysis')}</h3>
          <p className="text-sm text-muted-foreground">
            {weeklyStats.completedDays >= 5 
              ? t('reports.great')
              : weeklyStats.completedDays >= 3
              ? t('reports.good')
              : t('reports.start')
            }
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};

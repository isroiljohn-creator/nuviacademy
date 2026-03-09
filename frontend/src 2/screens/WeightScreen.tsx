import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Scale, Plus, TrendingDown, TrendingUp, Minus, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface WeightLog {
  id: string;
  weight: number;
  date: string;
}

interface WeightScreenProps {
  onBack?: () => void;
}

export const WeightScreen: React.FC<WeightScreenProps> = ({ onBack }) => {
  const { profile } = useUser();
  const { t, language } = useLanguage();
  const { vibrate } = useHaptic();
  const [weightLogs, setWeightLogs] = useState<WeightLog[]>([]);
  const [showInput, setShowInput] = useState(false);
  const [weightInput, setWeightInput] = useState(profile?.weight?.toString() || '70');

  useEffect(() => {
    const saved = localStorage.getItem('yasha_weight_logs');
    if (saved) {
      setWeightLogs(JSON.parse(saved));
    } else if (profile?.weight) {
      const initial: WeightLog = {
        id: '1',
        weight: profile.weight,
        date: new Date().toISOString().split('T')[0]
      };
      setWeightLogs([initial]);
      localStorage.setItem('yasha_weight_logs', JSON.stringify([initial]));
    }
  }, [profile?.weight]);

  const addWeight = () => {
    const weight = parseFloat(weightInput);
    if (isNaN(weight) || weight < 30 || weight > 300) {
      toast.error(t('weight.invalidWeight'));
      return;
    }

    vibrate('success');
    const today = new Date().toISOString().split('T')[0];
    const existingIndex = weightLogs.findIndex(l => l.date === today);
    let newLogs: WeightLog[];

    if (existingIndex >= 0) {
      newLogs = weightLogs.map((l, i) => i === existingIndex ? { ...l, weight } : l);
    } else {
      const newLog: WeightLog = {
        id: Date.now().toString(),
        weight,
        date: today
      };
      newLogs = [...weightLogs, newLog];
    }

    setWeightLogs(newLogs);
    localStorage.setItem('yasha_weight_logs', JSON.stringify(newLogs));
    setShowInput(false);
    toast.success(t('weight.saved'));
  };

  const currentWeight = weightLogs.length > 0 ? weightLogs[weightLogs.length - 1].weight : profile?.weight || 70;
  const startWeight = weightLogs.length > 0 ? weightLogs[0].weight : profile?.weight || 70;
  const weightChange = currentWeight - startWeight;
  const goalWeight = profile?.goal === 'lose' ? startWeight - 5 : profile?.goal === 'gain' ? startWeight + 5 : startWeight;

  const chartData = weightLogs.slice(-14).map(log => ({
    date: new Date(log.date).toLocaleDateString(language === 'ru' ? 'ru' : 'uz', { day: '2-digit', month: 'short' }),
    weight: log.weight
  }));

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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {onBack && (
              <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <div>
              <h1 className="text-xl font-bold text-foreground">{t('weight.title')}</h1>
              <p className="text-sm text-muted-foreground">{t('weight.subtitle')}</p>
            </div>
          </div>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-4 space-y-4"
      >
        {/* Current weight card */}
        <motion.div
          variants={itemVariants}
          className="p-5 rounded-2xl bg-gradient-to-br from-blue-500/15 to-blue-500/5 border border-blue-500/30"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Scale className="w-7 h-7 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{t('weight.current')}</p>
                <p className="text-3xl font-bold text-foreground">{currentWeight} kg</p>
              </div>
            </div>
            <Button
              size="icon"
              onClick={() => {
                vibrate('light');
                setShowInput(!showInput);
              }}
              className="w-12 h-12 rounded-xl"
            >
              {showInput ? <Minus className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            </Button>
          </div>

          {showInput && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex flex-col gap-3 mt-4"
            >
              <input
                type="number"
                value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                step="0.1"
                className="w-full h-12 px-4 rounded-xl bg-background border border-border text-foreground text-center text-lg font-medium"
                placeholder={t('weight.placeholder')}
                autoFocus
              />
              <Button onClick={addWeight} className="w-full h-12">
                {t('common.save')}
              </Button>
            </motion.div>
          )}
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-card border border-border/50"
          >
            <div className="flex items-center gap-2 mb-2">
              {weightChange <= 0 ? (
                <TrendingDown className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingUp className="w-5 h-5 text-orange-400" />
              )}
              <span className="text-sm text-muted-foreground">{t('weight.change')}</span>
            </div>
            <p className={`text-2xl font-bold ${weightChange <= 0 ? 'text-green-400' : 'text-orange-400'}`}>
              {weightChange > 0 ? '+' : ''}{weightChange.toFixed(1)} kg
            </p>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-card border border-border/50"
          >
            <div className="flex items-center gap-2 mb-2">
              <Scale className="w-5 h-5 text-primary" />
              <span className="text-sm text-muted-foreground">{t('weight.goal')}</span>
            </div>
            <p className="text-2xl font-bold text-foreground">{goalWeight} kg</p>
          </motion.div>
        </div>

        {/* Chart */}
        {chartData.length > 1 && (
          <motion.div
            variants={itemVariants}
            className="p-4 rounded-2xl bg-card border border-border/50"
          >
            <h3 className="font-semibold text-foreground mb-4">{t('weight.last14days')}</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis
                    dataKey="date"
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={['dataMin - 1', 'dataMax + 1']}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={35}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '12px',
                      fontSize: '13px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="weight"
                    stroke="hsl(200, 80%, 50%)"
                    strokeWidth={3}
                    dot={{ fill: 'hsl(200, 80%, 50%)', strokeWidth: 0, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* History */}
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-2xl bg-card border border-border/50"
        >
          <h3 className="font-semibold text-foreground mb-4">{t('weight.history')}</h3>
          <div className="space-y-3 max-h-48 overflow-y-auto">
            {weightLogs.slice().reverse().slice(0, 10).map((log) => (
              <div key={log.id} className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
                <span className="text-sm text-muted-foreground">
                  {new Date(log.date).toLocaleDateString(language === 'ru' ? 'ru' : 'uz', { day: 'numeric', month: 'long' })}
                </span>
                <span className="font-semibold text-foreground">{log.weight} kg</span>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

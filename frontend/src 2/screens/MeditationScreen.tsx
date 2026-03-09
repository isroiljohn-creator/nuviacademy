import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Wind, Play, Pause, RotateCcw, Moon, Sun, Waves, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

type BreathPhase = 'inhale' | 'hold' | 'exhale' | 'rest';

interface BreathingPattern {
  id: string;
  nameKey: string;
  descKey: string;
  icon: React.ReactNode;
  inhale: number;
  hold: number;
  exhale: number;
  rest: number;
  color: string;
  tipKey: string;
}

interface MeditationScreenProps {
  onBack?: () => void;
}

export const MeditationScreen: React.FC<MeditationScreenProps> = ({ onBack }) => {
  const { t } = useLanguage();
  const { vibrate } = useHaptic();

  const patterns: BreathingPattern[] = [
    {
      id: 'relaxing',
      nameKey: 'meditation.relaxing',
      descKey: 'meditation.relaxingDesc',
      icon: <Moon className="w-5 h-5" />,
      inhale: 4,
      hold: 7,
      exhale: 8,
      rest: 0,
      color: 'purple',
      tipKey: 'meditation.relaxingTip'
    },
    {
      id: 'energizing',
      nameKey: 'meditation.energizing',
      descKey: 'meditation.energizingDesc',
      icon: <Sun className="w-5 h-5" />,
      inhale: 4,
      hold: 4,
      exhale: 4,
      rest: 0,
      color: 'orange',
      tipKey: 'meditation.energizingTip'
    },
    {
      id: 'calm',
      nameKey: 'meditation.calm',
      descKey: 'meditation.calmDesc',
      icon: <Waves className="w-5 h-5" />,
      inhale: 5,
      hold: 2,
      exhale: 5,
      rest: 2,
      color: 'blue',
      tipKey: 'meditation.calmTip'
    }
  ];

  const [selectedPattern, setSelectedPattern] = useState<BreathingPattern>(patterns[0]);
  const [isActive, setIsActive] = useState(false);
  const [phase, setPhase] = useState<BreathPhase>('inhale');
  const [timeLeft, setTimeLeft] = useState(selectedPattern.inhale);
  const [cycles, setCycles] = useState(0);

  const phaseLabels: Record<BreathPhase, string> = {
    inhale: t('meditation.inhale'),
    hold: t('meditation.hold'),
    exhale: t('meditation.exhale'),
    rest: t('meditation.rest')
  };

  React.useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          vibrate('light');
          
          if (phase === 'inhale') {
            if (selectedPattern.hold > 0) {
              setPhase('hold');
              return selectedPattern.hold;
            } else {
              setPhase('exhale');
              return selectedPattern.exhale;
            }
          } else if (phase === 'hold') {
            setPhase('exhale');
            return selectedPattern.exhale;
          } else if (phase === 'exhale') {
            if (selectedPattern.rest > 0) {
              setPhase('rest');
              return selectedPattern.rest;
            } else {
              setPhase('inhale');
              setCycles(c => c + 1);
              return selectedPattern.inhale;
            }
          } else {
            setPhase('inhale');
            setCycles(c => c + 1);
            return selectedPattern.inhale;
          }
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, phase, selectedPattern, vibrate]);

  const toggleActive = () => {
    vibrate('medium');
    if (!isActive) {
      setPhase('inhale');
      setTimeLeft(selectedPattern.inhale);
      setCycles(0);
    }
    setIsActive(!isActive);
  };

  const reset = () => {
    vibrate('light');
    setIsActive(false);
    setPhase('inhale');
    setTimeLeft(selectedPattern.inhale);
    setCycles(0);
  };

  const selectPattern = (pattern: BreathingPattern) => {
    vibrate('selection');
    setSelectedPattern(pattern);
    setPhase('inhale');
    setTimeLeft(pattern.inhale);
    setCycles(0);
    setIsActive(false);
  };

  const getCircleScale = () => {
    if (phase === 'inhale') return 1.2;
    if (phase === 'exhale') return 0.85;
    return 1;
  };

  const getColorStyles = (color: string, isSelected: boolean) => {
    const colors: Record<string, { bg: string; border: string; icon: string }> = {
      purple: {
        bg: isSelected ? 'bg-purple-500/20' : 'bg-card',
        border: isSelected ? 'border-purple-500/50' : 'border-border/50',
        icon: 'text-purple-400'
      },
      orange: {
        bg: isSelected ? 'bg-orange-500/20' : 'bg-card',
        border: isSelected ? 'border-orange-500/50' : 'border-border/50',
        icon: 'text-orange-400'
      },
      blue: {
        bg: isSelected ? 'bg-blue-500/20' : 'bg-card',
        border: isSelected ? 'border-blue-500/50' : 'border-border/50',
        icon: 'text-blue-400'
      },
    };
    return colors[color] || { bg: 'bg-card', border: 'border-border/50', icon: 'text-primary' };
  };

  const getCircleColor = (color: string) => {
    const colors: Record<string, string> = {
      purple: 'border-purple-500/60',
      orange: 'border-orange-500/60',
      blue: 'border-blue-500/60',
    };
    return colors[color] || 'border-primary/60';
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          {onBack && (
            <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('meditation.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('meditation.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Pattern selection - Symmetrical cards */}
      <div className="px-4 mb-8">
        <div className="grid grid-cols-3 gap-2">
          {patterns.map((pattern) => {
            const styles = getColorStyles(pattern.color, selectedPattern.id === pattern.id);
            return (
              <button
                key={pattern.id}
                onClick={() => selectPattern(pattern)}
                className={`p-3 rounded-2xl border-2 transition-all ${styles.bg} ${styles.border}`}
              >
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center mx-auto mb-2 bg-card/50 ${styles.icon}`}>
                  {pattern.icon}
                </div>
                <h3 className="font-medium text-foreground text-xs text-center leading-tight">{t(pattern.nameKey)}</h3>
                <p className="text-[9px] text-muted-foreground text-center mt-0.5 leading-tight">{t(pattern.descKey)}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Breathing circle - Centered and clean */}
      <div className="flex flex-col items-center justify-center px-4">
        <div className="relative w-52 h-52 flex items-center justify-center mb-6">
          {/* Outer glow */}
          <motion.div
            animate={{ 
              scale: getCircleScale(),
              opacity: isActive ? 0.4 : 0.2
            }}
            transition={{ 
              duration: phase === 'inhale' ? selectedPattern.inhale : 
                       phase === 'exhale' ? selectedPattern.exhale : 0.5,
              ease: 'easeInOut'
            }}
            className={`absolute w-full h-full rounded-full bg-primary/20 blur-2xl`}
          />
          
          {/* Main circle */}
          <motion.div
            animate={{ scale: getCircleScale() }}
            transition={{ 
              duration: phase === 'inhale' ? selectedPattern.inhale : 
                       phase === 'exhale' ? selectedPattern.exhale : 0.5,
              ease: 'easeInOut'
            }}
            className={`relative w-44 h-44 rounded-full bg-card/80 border-4 ${getCircleColor(selectedPattern.color)} flex items-center justify-center shadow-xl`}
          >
            <div className="text-center">
              <motion.p
                key={phase}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-base font-semibold text-muted-foreground mb-1"
              >
                {phaseLabels[phase]}
              </motion.p>
              <p className="text-5xl font-bold text-primary">{timeLeft}</p>
            </div>
          </motion.div>
        </div>

        {/* Cycles counter */}
        <p className="text-muted-foreground text-sm mb-6">
          {t('meditation.cycles')}: <span className="font-bold text-foreground text-lg">{cycles}</span>
        </p>

        {/* Controls - Symmetrical */}
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={reset}
            className="w-14 h-14 rounded-xl border-2"
          >
            <RotateCcw className="w-5 h-5" />
          </Button>
          
          <Button
            size="icon"
            onClick={toggleActive}
            className="w-16 h-16 rounded-xl"
          >
            {isActive ? (
              <Pause className="w-7 h-7" />
            ) : (
              <Play className="w-7 h-7 ml-0.5" />
            )}
          </Button>
        </div>
      </div>

      {/* Tips - Clean card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mx-4 mt-8 p-4 rounded-2xl bg-card border border-border/50"
      >
        <div className="flex items-start gap-3">
          <div className="text-2xl">💡</div>
          <div>
            <h3 className="font-semibold text-foreground text-sm mb-1">{t('meditation.tip')}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {t(selectedPattern.tipKey)}
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

import React from 'react';
import { motion } from 'framer-motion';
import { Plus, Check, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ProgressRing } from './ProgressRing';
import { useHaptic } from '@/hooks/useHaptic';

interface HabitCardProps {
  icon: React.ReactNode;
  title: string;
  current: number;
  target: number;
  unit: string;
  streak?: number;
  onAdd?: () => void;
  addAmount?: number;
  isCompleted?: boolean;
}

export const HabitCard: React.FC<HabitCardProps> = ({
  icon,
  title,
  current,
  target,
  unit,
  streak = 0,
  onAdd,
  addAmount,
  isCompleted = false,
}) => {
  const { vibrate } = useHaptic();
  const progress = Math.min((current / target) * 100, 100);

  const handleAdd = () => {
    vibrate('success');
    onAdd?.();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-4 rounded-2xl bg-card border border-border/50 transition-all",
        isCompleted && "border-success/30"
      )}
    >
      <div className="flex items-center gap-4">
        <ProgressRing 
          progress={progress} 
          size={64} 
          strokeWidth={6}
          color={isCompleted ? 'success' : 'primary'}
        >
          <div className={cn(
            "w-8 h-8 flex items-center justify-center",
            isCompleted ? "text-success" : "text-primary"
          )}>
            {icon}
          </div>
        </ProgressRing>
        
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground">{title}</h3>
            {streak > 0 && (
              <span className="flex items-center gap-1 text-xs text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded-full">
                <Flame className="w-3 h-3" />
                {streak} kun
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {current} / {target} {unit}
          </p>
        </div>
        
        {onAdd && !isCompleted && (
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleAdd}
            className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center text-primary hover:bg-primary/30 transition-colors"
          >
            <Plus className="w-6 h-6" />
          </motion.button>
        )}
        
        {isCompleted && (
          <div className="w-12 h-12 rounded-xl bg-success/20 flex items-center justify-center">
            <Check className="w-6 h-6 text-success" />
          </div>
        )}
      </div>
      
      {addAmount && !isCompleted && (
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Bosing: +{addAmount} {unit}
        </p>
      )}
    </motion.div>
  );
};

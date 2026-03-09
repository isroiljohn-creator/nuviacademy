import React from 'react';
import { motion } from 'framer-motion';
import { Play, Lock, Clock, Flame, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHaptic } from '@/hooks/useHaptic';

interface WorkoutCardProps {
  title: string;
  duration: string;
  calories: number;
  exercises: number;
  isLocked?: boolean;
  isCompleted?: boolean;
  onClick?: () => void;
}

export const WorkoutCard: React.FC<WorkoutCardProps> = ({
  title,
  duration,
  calories,
  exercises,
  isLocked = false,
  isCompleted = false,
  onClick,
}) => {
  const { vibrate } = useHaptic();

  const handleClick = () => {
    vibrate('light');
    onClick?.();
  };

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={handleClick}
      className={cn(
        "w-full p-4 rounded-2xl bg-card border border-border/50 text-left transition-all",
        isLocked && "opacity-60",
        isCompleted && "border-success/30 bg-success/5",
        !isLocked && !isCompleted && "hover:border-primary/30"
      )}
    >
      <div className="flex items-center gap-3">
        {/* Icon - fixed size */}
        <div className={cn(
          "w-12 h-12 rounded-xl flex items-center justify-center shrink-0",
          isCompleted ? "bg-success/20" : isLocked ? "bg-muted" : "bg-primary/20"
        )}>
          {isCompleted ? (
            <CheckCircle2 className="w-6 h-6 text-success" />
          ) : isLocked ? (
            <Lock className="w-5 h-5 text-muted-foreground" />
          ) : (
            <Play className="w-5 h-5 text-primary" />
          )}
        </div>
        
        {/* Content - flex grow */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-foreground truncate">{title}</h3>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {duration}
            </span>
            <span className="flex items-center gap-1">
              <Flame className="w-3.5 h-3.5" />
              {calories} kcal
            </span>
          </div>
        </div>
        
        {/* Exercise count - fixed width */}
        <div className="text-center shrink-0">
          <span className="text-xl font-bold text-foreground">{exercises}</span>
          <p className="text-[10px] text-muted-foreground">mashq</p>
        </div>
      </div>
    </motion.button>
  );
};
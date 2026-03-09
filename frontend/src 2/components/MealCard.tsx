import React from 'react';
import { motion } from 'framer-motion';
import { Lock, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHaptic } from '@/hooks/useHaptic';

interface MealCardProps {
  time: string;
  title: string;
  calories: number;
  items: string[];
  isLocked?: boolean;
  onClick?: () => void;
}

export const MealCard: React.FC<MealCardProps> = ({
  time,
  title,
  calories,
  items,
  isLocked = false,
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
        isLocked ? "opacity-60" : "hover:border-primary/30"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wide">
              {time}
            </span>
            {isLocked && (
              <Lock className="w-3 h-3 text-muted-foreground" />
            )}
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
          <p className="text-sm text-primary font-medium">{calories} kkal</p>
          
          {!isLocked && (
            <div className="mt-3 flex flex-wrap gap-1">
              {items.slice(0, 3).map((item, index) => (
                <span
                  key={index}
                  className="text-xs px-2 py-1 rounded-lg bg-muted text-muted-foreground"
                >
                  {item}
                </span>
              ))}
              {items.length > 3 && (
                <span className="text-xs px-2 py-1 rounded-lg bg-muted text-muted-foreground">
                  +{items.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
        
        <ChevronRight className={cn(
          "w-5 h-5 mt-1",
          isLocked ? "text-muted-foreground" : "text-primary"
        )} />
      </div>
    </motion.button>
  );
};

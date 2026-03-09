import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  target?: string | number;
  unit?: string;
  progress?: number;
  color?: 'primary' | 'blue' | 'orange' | 'purple' | 'red';
  onClick?: () => void;
}

const colorStyles = {
  primary: {
    bg: 'bg-primary/10',
    icon: 'text-primary',
    progress: 'bg-primary',
  },
  blue: {
    bg: 'bg-blue-500/10',
    icon: 'text-blue-400',
    progress: 'bg-blue-500',
  },
  orange: {
    bg: 'bg-orange-500/10',
    icon: 'text-orange-400',
    progress: 'bg-orange-500',
  },
  purple: {
    bg: 'bg-purple-500/10',
    icon: 'text-purple-400',
    progress: 'bg-purple-500',
  },
  red: {
    bg: 'bg-red-500/10',
    icon: 'text-red-400',
    progress: 'bg-red-500',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  icon: Icon,
  label,
  value,
  target,
  unit,
  progress,
  color = 'primary',
  onClick,
}) => {
  const styles = colorStyles[color];

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "flex flex-col p-4 rounded-2xl bg-card border border-border/50 text-left w-full min-h-[120px]",
        onClick && "cursor-pointer active:bg-card/80"
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className={cn("p-2 rounded-xl", styles.bg)}>
          <Icon className={cn("w-4 h-4", styles.icon)} />
        </div>
        <span className="text-xs font-medium text-muted-foreground break-words leading-tight">{label}</span>
      </div>

      <div className="flex items-baseline gap-1 mt-auto">
        <span className="text-xl font-bold text-foreground">{value}</span>
        {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
        {target && (
          <span className="text-xs text-muted-foreground">/ {target}</span>
        )}
      </div>

      {typeof progress === 'number' && (
        <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
          <motion.div
            className={cn("h-full rounded-full", styles.progress)}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(progress, 100)}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      )}
    </motion.button>
  );
};
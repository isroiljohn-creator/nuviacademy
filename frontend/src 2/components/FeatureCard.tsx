import React from 'react';
import { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  value?: string | number;
  color?: 'blue' | 'orange' | 'purple' | 'green' | 'amber' | 'red' | 'cyan' | 'pink' | 'primary';
  onClick?: () => void;
}

const colorMap = {
  blue: 'from-blue-500/15 to-blue-500/5 border-blue-500/30 text-blue-400',
  orange: 'from-orange-500/15 to-orange-500/5 border-orange-500/30 text-orange-400',
  purple: 'from-purple-500/15 to-purple-500/5 border-purple-500/30 text-purple-400',
  green: 'from-green-500/15 to-green-500/5 border-green-500/30 text-green-400',
  amber: 'from-amber-500/15 to-amber-500/5 border-amber-500/30 text-amber-400',
  red: 'from-red-500/15 to-red-500/5 border-red-500/30 text-red-400',
  cyan: 'from-cyan-500/15 to-cyan-500/5 border-cyan-500/30 text-cyan-400',
  pink: 'from-pink-500/15 to-pink-500/5 border-pink-500/30 text-pink-400',
  primary: 'from-primary/15 to-primary/5 border-primary/30 text-primary',
};

const iconBgMap = {
  blue: 'bg-blue-500/20',
  orange: 'bg-orange-500/20',
  purple: 'bg-purple-500/20',
  green: 'bg-green-500/20',
  amber: 'bg-amber-500/20',
  red: 'bg-red-500/20',
  cyan: 'bg-cyan-500/20',
  pink: 'bg-pink-500/20',
  primary: 'bg-primary/20',
};

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon: Icon,
  title,
  subtitle,
  value,
  color = 'primary',
  onClick
}) => {
  const colorClasses = colorMap[color];
  const iconBg = iconBgMap[color];

  return (
    <button
      onClick={onClick}
      className={`w-full p-4 rounded-2xl bg-gradient-to-br ${colorClasses} border text-left transition-all active:scale-[0.98]`}
    >
      <div className={`w-12 h-12 rounded-xl ${iconBg} flex items-center justify-center mb-3`}>
        <Icon className="w-6 h-6" />
      </div>
      {value !== undefined && (
        <p className="text-2xl font-bold text-foreground mb-1">{value}</p>
      )}
      <p className="text-sm font-semibold text-foreground">{title}</p>
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
      )}
    </button>
  );
};
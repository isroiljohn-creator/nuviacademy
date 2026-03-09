import React from 'react';
import { Lock } from 'lucide-react';

interface Day {
  day: string;
  date: number;
  isToday: boolean;
}

interface DaySelectorProps {
  days: Day[];
  selectedDay: number;
  onDaySelect: (index: number) => void;
  isPremium?: boolean;
}

export const DaySelector: React.FC<DaySelectorProps> = ({
  days,
  selectedDay,
  onDaySelect,
  isPremium = false
}) => {
  return (
    <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 px-1 -mx-1">
      {days.map((day, index) => {
        const isLocked = index > 0 && !isPremium;
        const isSelected = selectedDay === index;

        return (
          <button
            key={index}
            onClick={() => onDaySelect(index)}
            className={`relative flex flex-col items-center min-w-[54px] py-3 px-2 rounded-2xl transition-all duration-300 border ${isSelected
                ? 'bg-primary text-primary-foreground border-primary shadow-glow-sm scale-105 z-10'
                : 'bg-card text-foreground border-border/50 hover:border-primary/30'
              } ${isLocked ? 'opacity-60 grayscale-[0.5]' : ''}`}
          >
            <span className={`text-[10px] font-medium mb-1 uppercase tracking-wider ${isSelected ? 'opacity-90' : 'text-muted-foreground'}`}>{day.day}</span>
            <span className="text-lg font-extrabold">{day.date}</span>
            {day.isToday && !isSelected && (
              <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary" />
            )}
            {isLocked && (
              <div className="absolute -top-1 -right-1 p-1 rounded-full bg-background border border-border/50 shadow-sm">
                <Lock className="w-2.5 h-2.5 text-muted-foreground" />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
};
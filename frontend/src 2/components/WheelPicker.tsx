import React, { useRef, useEffect, useState } from 'react';
import { useHaptic } from '@/hooks/useHaptic';

interface WheelPickerProps {
  items: (string | number)[];
  value: string | number;
  onChange: (value: string | number) => void;
  label?: string;
  suffix?: string;
  itemHeight?: number;
  visibleItems?: number;
}

export const WheelPicker: React.FC<WheelPickerProps> = ({
  items,
  value,
  onChange,
  label,
  suffix,
  itemHeight = 40,
  visibleItems = 5,
}) => {
  const { vibrate } = useHaptic();
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const lastValueRef = useRef(value);

  const containerHeight = itemHeight * visibleItems;
  const centerOffset = (containerHeight - itemHeight) / 2;
  const selectedIndex = items.indexOf(value);

  useEffect(() => {
    if (containerRef.current && !isDragging) {
      containerRef.current.scrollTop = selectedIndex * itemHeight;
    }
  }, [selectedIndex, itemHeight, isDragging]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    
    const scrollTop = containerRef.current.scrollTop;
    const index = Math.round(scrollTop / itemHeight);
    const clampedIndex = Math.max(0, Math.min(index, items.length - 1));
    const newValue = items[clampedIndex];
    
    if (newValue !== lastValueRef.current) {
      lastValueRef.current = newValue;
      vibrate('selection');
      onChange(newValue);
    }
  };

  const handleScrollEnd = () => {
    setIsDragging(false);
    if (!containerRef.current) return;
    
    const scrollTop = containerRef.current.scrollTop;
    const index = Math.round(scrollTop / itemHeight);
    const clampedIndex = Math.max(0, Math.min(index, items.length - 1));
    
    containerRef.current.scrollTo({
      top: clampedIndex * itemHeight,
      behavior: 'smooth'
    });
    
    vibrate('light');
  };

  return (
    <div className="flex flex-col items-center">
      {label && (
        <span className="text-xs text-muted-foreground mb-2 font-medium">{label}</span>
      )}
      <div 
        className="relative overflow-hidden rounded-xl bg-card border border-border/50"
        style={{ height: containerHeight, width: '100%' }}
      >
        {/* Selection indicator */}
        <div 
          className="absolute left-1 right-1 pointer-events-none z-10 border-y-2 border-primary/50 bg-primary/10 rounded-lg"
          style={{ 
            top: centerOffset,
            height: itemHeight,
          }}
        />
        
        {/* Gradient overlays */}
        <div 
          className="absolute top-0 left-0 right-0 pointer-events-none z-20 rounded-t-xl"
          style={{
            height: centerOffset,
            background: 'linear-gradient(to bottom, hsl(var(--card)), transparent)'
          }}
        />
        <div 
          className="absolute bottom-0 left-0 right-0 pointer-events-none z-20 rounded-b-xl"
          style={{
            height: centerOffset,
            background: 'linear-gradient(to top, hsl(var(--card)), transparent)'
          }}
        />

        {/* Scroll container */}
        <div
          ref={containerRef}
          className="h-full overflow-y-auto scrollbar-hide"
          style={{ 
            scrollSnapType: 'y mandatory',
            paddingTop: centerOffset,
            paddingBottom: centerOffset,
          }}
          onScroll={handleScroll}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={handleScrollEnd}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={handleScrollEnd}
          onMouseLeave={() => isDragging && handleScrollEnd()}
        >
          {items.map((item, index) => {
            const isSelected = item === value;
            const distance = Math.abs(index - selectedIndex);
            const opacity = isSelected ? 1 : Math.max(0.3, 1 - distance * 0.25);
            const scale = isSelected ? 1 : Math.max(0.85, 1 - distance * 0.05);
            
            return (
              <div
                key={index}
                className="flex items-center justify-center cursor-pointer transition-all duration-150"
                style={{ 
                  height: itemHeight,
                  scrollSnapAlign: 'center',
                  transform: `scale(${scale})`,
                  opacity,
                }}
                onClick={() => {
                  vibrate('selection');
                  onChange(item);
                  if (containerRef.current) {
                    containerRef.current.scrollTo({
                      top: index * itemHeight,
                      behavior: 'smooth'
                    });
                  }
                }}
              >
                <span className={`text-lg font-bold tabular-nums ${
                  isSelected ? 'text-primary' : 'text-muted-foreground'
                }`}>
                  {item}
                  {suffix && isSelected && (
                    <span className="text-sm font-normal ml-1">{suffix}</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

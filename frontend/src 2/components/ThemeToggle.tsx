import React, { useEffect, useState, forwardRef } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useHaptic } from '@/hooks/useHaptic';

export const ThemeToggle = forwardRef<HTMLButtonElement, React.HTMLAttributes<HTMLButtonElement>>((props, ref) => {
  const { vibrate } = useHaptic();
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('yasha_theme');
    return saved ? saved === 'dark' : true;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.remove('light');
    } else {
      root.classList.add('light');
    }
    localStorage.setItem('yasha_theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggle = () => {
    vibrate('medium');
    setIsDark(!isDark);
  };

  return (
    <button
      ref={ref}
      onClick={toggle}
      className="relative w-16 h-8 rounded-full bg-muted border border-border transition-colors"
      {...props}
    >
      <motion.div
        className="absolute top-1 w-6 h-6 rounded-full bg-primary flex items-center justify-center"
        animate={{
          x: isDark ? 4 : 32,
        }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        {isDark ? (
          <Moon className="w-3.5 h-3.5 text-primary-foreground" />
        ) : (
          <Sun className="w-3.5 h-3.5 text-primary-foreground" />
        )}
      </motion.div>
    </button>
  );
});

ThemeToggle.displayName = 'ThemeToggle';

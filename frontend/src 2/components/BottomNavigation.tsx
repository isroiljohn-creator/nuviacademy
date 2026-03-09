import React from 'react';
import { motion } from 'framer-motion';
import { Home, Compass, UtensilsCrossed, Dumbbell, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHaptic } from '@/hooks/useHaptic';
import { useLanguage } from '@/contexts/LanguageContext';

interface TabItem {
  id: string;
  labelKey: string;
  icon: React.ReactNode;
}

const tabs: TabItem[] = [
  { id: 'home', labelKey: 'nav.home', icon: <Home /> },
  { id: 'explore', labelKey: 'nav.explore', icon: <Compass /> },
  { id: 'menu', labelKey: 'nav.menu', icon: <UtensilsCrossed /> },
  { id: 'workout', labelKey: 'nav.workout', icon: <Dumbbell /> },
  { id: 'profile', labelKey: 'nav.profile', icon: <User /> },
];

interface BottomNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const BottomNavigation: React.FC<BottomNavigationProps> = ({
  activeTab,
  onTabChange,
}) => {
  const { vibrate } = useHaptic();
  const { t } = useLanguage();

  const handleTabChange = (tabId: string) => {
    vibrate('light');
    onTabChange(tabId);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40">
      <div className="bg-card/98 backdrop-blur-xl border-t border-border/60 shadow-lg safe-area-bottom">
        <div className="flex items-center justify-around px-2 py-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={cn(
                  "relative flex flex-col items-center justify-center flex-1 py-2 px-1 rounded-xl transition-all duration-200",
                  isActive ? "text-primary bg-primary/10" : "text-muted-foreground"
                )}
              >
                <motion.div
                  className="w-6 h-6 mb-1 relative z-10"
                  animate={{
                    scale: isActive ? 1.2 : 1,
                    y: isActive ? -2 : 0
                  }}
                  transition={{ type: "spring", stiffness: 500, damping: 15 }}
                >
                  {tab.icon}
                </motion.div>
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-x-1 inset-y-1 bg-primary/10 rounded-xl -z-0"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
                <span className={cn(
                  "text-[11px] font-medium leading-tight",
                  isActive ? "opacity-100" : "opacity-70"
                )}>
                  {t(tab.labelKey)}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
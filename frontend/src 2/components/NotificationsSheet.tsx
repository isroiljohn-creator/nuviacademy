import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Bell, Droplets, Dumbbell, Moon, Utensils } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';

interface NotificationsSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NotificationSettings {
  waterReminder: boolean;
  workoutReminder: boolean;
  sleepReminder: boolean;
  mealReminder: boolean;
}

export const NotificationsSheet: React.FC<NotificationsSheetProps> = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  
  const [settings, setSettings] = useState<NotificationSettings>(() => {
    const saved = localStorage.getItem('yasha_notifications');
    return saved ? JSON.parse(saved) : {
      waterReminder: true,
      workoutReminder: true,
      sleepReminder: false,
      mealReminder: true,
    };
  });

  useEffect(() => {
    localStorage.setItem('yasha_notifications', JSON.stringify(settings));
  }, [settings]);

  if (!isOpen) return null;

  const handleToggle = (key: keyof NotificationSettings) => {
    vibrate('medium');
    setSettings(prev => {
      const newValue = !prev[key];
      toast.success(newValue ? t('notifications.enabled') : t('notifications.disabled'));
      return { ...prev, [key]: newValue };
    });
  };

  const handleClose = () => {
    vibrate('light');
    onClose();
  };

  const notifications = [
    { key: 'waterReminder' as const, icon: Droplets, labelKey: 'notifications.water', descKey: 'notifications.waterDesc', color: 'text-blue-400' },
    { key: 'workoutReminder' as const, icon: Dumbbell, labelKey: 'notifications.workout', descKey: 'notifications.workoutDesc', color: 'text-orange-400' },
    { key: 'sleepReminder' as const, icon: Moon, labelKey: 'notifications.sleep', descKey: 'notifications.sleepDesc', color: 'text-purple-400' },
    { key: 'mealReminder' as const, icon: Utensils, labelKey: 'notifications.meal', descKey: 'notifications.mealDesc', color: 'text-green-400' },
  ];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm overflow-auto"
      >
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between p-4 border-b border-border bg-background/80 backdrop-blur-lg safe-area-top z-10">
          <button onClick={handleClose} className="text-muted-foreground">
            <X className="w-6 h-6" />
          </button>
          <h2 className="text-lg font-bold text-foreground">{t('notifications.title')}</h2>
          <div className="w-6" />
        </div>

        <div className="p-4 pb-28 space-y-3">
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-primary/10 border border-primary/30 mb-6">
            <Bell className="w-6 h-6 text-primary" />
            <p className="text-sm text-foreground">
              {t('notifications.info')}
            </p>
          </div>

          {notifications.map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 rounded-2xl bg-card border border-border/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
                  <item.icon className={`w-5 h-5 ${item.color}`} />
                </div>
                <div>
                  <p className="font-medium text-foreground">{t(item.labelKey)}</p>
                  <p className="text-xs text-muted-foreground">{t(item.descKey)}</p>
                </div>
              </div>
              <Switch
                checked={settings[item.key]}
                onCheckedChange={() => handleToggle(item.key)}
              />
            </div>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

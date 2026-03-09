import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Shield, Lock, Eye, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';

interface PrivacySheetProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PrivacySheet: React.FC<PrivacySheetProps> = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const { resetData } = useUser();

  if (!isOpen) return null;

  const handleClose = () => {
    vibrate('light');
    onClose();
  };

  const handleClearData = async () => {
    vibrate('error');
    if (confirm(t('privacy.confirmDelete'))) {
      await resetData();
      toast.success(t('privacy.deleted'));
      onClose();
      // resetData handles state reset, navigation/reload can be handled here or inside context.
      // Context reload page logic was removed in favor of state reset. 
      // If we want to force reload to show onboarding, we can do it here.
      window.location.reload();
    }
  };

  const privacyItems = [
    {
      icon: Lock,
      titleKey: 'privacy.dataSecurity',
      descKey: 'privacy.dataSecurityDesc',
    },
    {
      icon: Eye,
      titleKey: 'privacy.policy',
      descKey: 'privacy.policyDesc',
    },
    {
      icon: Shield,
      titleKey: 'privacy.encryption',
      descKey: 'privacy.encryptionDesc',
    },
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
          <h2 className="text-lg font-bold text-foreground">{t('privacy.title')}</h2>
          <div className="w-6" />
        </div>

        <div className="p-4 pb-28 space-y-4">
          {privacyItems.map((item, index) => (
            <div key={index} className="p-4 rounded-2xl bg-card border border-border/50">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">{t(item.titleKey)}</h3>
                  <p className="text-sm text-muted-foreground">{t(item.descKey)}</p>
                </div>
              </div>
            </div>
          ))}

          {/* Clear data */}
          <div className="mt-8 p-4 rounded-2xl bg-destructive/10 border border-destructive/30">
            <div className="flex items-start gap-3 mb-4">
              <Trash2 className="w-5 h-5 text-destructive flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-foreground mb-1">{t('privacy.deleteData')}</h3>
                <p className="text-sm text-muted-foreground">
                  {t('privacy.deleteDataDesc')}
                </p>
              </div>
            </div>
            <Button
              variant="destructive"
              className="w-full"
              onClick={handleClearData}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {t('privacy.deleteAll')}
            </Button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

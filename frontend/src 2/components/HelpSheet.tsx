import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, HelpCircle, MessageCircle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

interface HelpSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpSheet: React.FC<HelpSheetProps> = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  if (!isOpen) return null;

  const faqs = [
    { questionKey: 'help.faq1', answerKey: 'help.faq1Answer' },
    { questionKey: 'help.faq2', answerKey: 'help.faq2Answer' },
    { questionKey: 'help.faq3', answerKey: 'help.faq3Answer' },
    { questionKey: 'help.faq4', answerKey: 'help.faq4Answer' },
    { questionKey: 'help.faq5', answerKey: 'help.faq5Answer' },
  ];

  const handleClose = () => {
    vibrate('light');
    onClose();
  };

  const toggleFaq = (index: number) => {
    vibrate('selection');
    setOpenFaq(openFaq === index ? null : index);
  };

  const handleContactSupport = () => {
    vibrate('medium');
    window.open('https://t.me/yashabot', '_blank');
  };

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
          <h2 className="text-lg font-bold text-foreground">{t('help.title')}</h2>
          <div className="w-6" />
        </div>

        <div className="p-4 pb-28">
          {/* Contact support */}
          <div className="p-4 rounded-2xl bg-primary/10 border border-primary/30 mb-6">
            <div className="flex items-center gap-3 mb-3">
              <MessageCircle className="w-6 h-6 text-primary" />
              <h3 className="font-semibold text-foreground">{t('help.support')}</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              {t('help.supportDesc')}
            </p>
            <Button onClick={handleContactSupport} className="w-full">
              <ExternalLink className="w-4 h-4 mr-2" />
              {t('help.contactTelegram')}
            </Button>
          </div>

          {/* FAQs */}
          <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-primary" />
            {t('help.faq')}
          </h3>

          <div className="space-y-3">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                className="rounded-2xl bg-card border border-border/50 overflow-hidden"
              >
                <button
                  onClick={() => toggleFaq(index)}
                  className="w-full p-4 flex items-center justify-between text-left"
                >
                  <span className="font-medium text-foreground pr-4">{t(faq.questionKey)}</span>
                  {openFaq === index ? (
                    <ChevronUp className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  )}
                </button>
                <AnimatePresence>
                  {openFaq === index && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 text-sm text-muted-foreground">
                        {t(faq.answerKey)}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>

          {/* App version */}
          <div className="mt-8 text-center">
            <p className="text-sm text-muted-foreground">YASHA AI v1.0.0</p>
            <p className="text-xs text-muted-foreground mt-1">{t('help.copyright')}</p>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

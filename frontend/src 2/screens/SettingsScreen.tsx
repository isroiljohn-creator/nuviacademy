import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Globe, Moon, Sun, Monitor, Check } from 'lucide-react';
import { useLanguage, Language } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';

interface SettingsScreenProps {
  onBack?: () => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ onBack }) => {
  const { language, setLanguage, t } = useLanguage();
  const { vibrate } = useHaptic();

  const handleLanguageChange = (lang: Language) => {
    vibrate('medium');
    setLanguage(lang);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold text-foreground">{t('settings.title')}</h1>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-4"
        >
          {/* Language Section */}
          <motion.div variants={itemVariants}>
            <div className="flex items-center gap-2 mb-3">
              <Globe className="w-5 h-5 text-primary" />
              <h2 className="text-base font-semibold text-foreground">{t('settings.language')}</h2>
            </div>
            
            <div className="space-y-2">
              <button
                onClick={() => handleLanguageChange('uz')}
                className={`w-full p-4 rounded-xl border flex items-center justify-between transition-all ${
                  language === 'uz'
                    ? 'bg-primary/10 border-primary/50'
                    : 'bg-card border-border/50 hover:border-primary/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🇺🇿</span>
                  <div className="text-left">
                    <p className="font-semibold text-foreground">O'zbekcha</p>
                    <p className="text-sm text-muted-foreground">Uzbek</p>
                  </div>
                </div>
                {language === 'uz' && (
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
              </button>

              <button
                onClick={() => handleLanguageChange('ru')}
                className={`w-full p-4 rounded-xl border flex items-center justify-between transition-all ${
                  language === 'ru'
                    ? 'bg-primary/10 border-primary/50'
                    : 'bg-card border-border/50 hover:border-primary/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🇷🇺</span>
                  <div className="text-left">
                    <p className="font-semibold text-foreground">Русский</p>
                    <p className="text-sm text-muted-foreground">Russian</p>
                  </div>
                </div>
                {language === 'ru' && (
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
              </button>
            </div>
          </motion.div>

          {/* Info */}
          <motion.div
            variants={itemVariants}
            className="p-4 rounded-xl bg-primary/10 border border-primary/30"
          >
            <p className="text-sm text-foreground">
              {language === 'uz' 
                ? '💡 Tilni o\'zgartirsangiz, dastur interfeysi tanlangan tilda ko\'rsatiladi.'
                : '💡 При смене языка интерфейс приложения будет отображаться на выбранном языке.'
              }
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

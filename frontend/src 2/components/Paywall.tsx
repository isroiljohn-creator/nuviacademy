import React from 'react';
import { motion } from 'framer-motion';
import { Crown, Sparkles, Check, Lock, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';
import axios from 'axios';
import plansTable from '@/assets/plans_table.png';

interface PaywallProps {
  isOpen: boolean;
  onClose: () => void;
  feature?: string;
}

// Link to bot if needed as fallback
const TELEGRAM_BOT_URL = 'https://t.me/yashabot';

export const Paywall: React.FC<PaywallProps> = ({
  isOpen,
  onClose,
  feature,
}) => {
  const { t, language } = useLanguage();
  const { vibrate } = useHaptic();

  if (!isOpen) return null;

  const { planType } = useUser();
  const currentTier = planType?.toLowerCase();

  const plans = [
    {
      id: 'premium',
      name: '💎 PLUS',
      price: "49,000",
      periodKey: 'paywall.perMonth',
      descKey: 'paywall.premiumDesc',
      features: language === 'ru' ? [
        { text: 'AI Меню: Недельное (7 дней) персональное меню', included: true },
        { text: 'AI Тренировки: 7-дневный индивидуальный план', included: true },
        { text: 'Анализ калорий: до 3 раз в день', included: true, limited: true },
        { text: 'AI Тренер (Q&A): до 3 вопросов в день', included: true, limited: true },
      ] : [
        { text: 'AI Taomnoma: Haftalik (7 kunlik) shaxsiy menyu', included: true },
        { text: 'AI Mashg\'ulotlar: 7 kunlik individual mashqlar rejasi', included: true },
        { text: 'Kaloriya tahlili: Kuniga 3 martagacha', included: true, limited: true },
        { text: 'AI Murabbiy (QA): Kuniga 3 martagacha savol-javob', included: true, limited: true },
      ],
      popular: true,
      tier: 1
    },
    {
      id: 'vip',
      name: '👑 PRO',
      price: "97,000",
      periodKey: 'paywall.perMonth',
      descKey: 'paywall.vipDesc',
      features: language === 'ru' ? [
        { text: 'AI Меню: Обновляемое 4 раза в месяц (28 дней) меню', included: true },
        { text: 'Неограниченный анализ калорий', included: true, unlimited: true },
        { text: 'Неограниченный AI Тренер: Q&A', included: true, unlimited: true },
        { text: 'Неограниченные рецепты: AI здоровые рецепты', included: true, unlimited: true },
        { text: 'Список покупок: Список продуктов', included: true },
      ] : [
        { text: 'AI Taomnoma: Oyiga 4 marta yangilanadigan (28 kunlik) menyu', included: true },
        { text: 'Cheksiz Kaloriya tahlili', included: true, unlimited: true },
        { text: 'Cheksiz AI Murabbiy: Savol-javob', included: true, unlimited: true },
        { text: 'Cheksiz Retseptlar: AI bilan sog\'lom retseptlar', included: true, unlimited: true },
        { text: 'Shopping List: Mahsulotlar ro\'yxati', included: true },
      ],
      popular: false,
      tier: 2
    },
  ].filter(p => {
    // Hide Premium if user is VIP.
    if ((currentTier === 'vip' || currentTier === 'pro') && p.id === 'premium') return false;
    // Hide Premium if user is already Premium (optional, but logical)
    if ((currentTier === 'premium' || currentTier === 'plus') && p.id === 'premium') return false;
    return true;
  });

  const handleSubscribe = async (planId: string) => {
    vibrate('success');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/pay/invoice', {
        plan_id: planId
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.invoice_link) {
        // @ts-ignore
        if (window.Telegram?.WebApp?.openInvoice) {
          // @ts-ignore
          window.Telegram.WebApp.openInvoice(response.data.invoice_link, (status: string) => {
            if (status === 'paid') {
              toast.success(t('paywall.success'));
              onClose();
            } else if (status === 'failed') {
              toast.error(t('paywall.failed'));
            }
          });
        } else {
          // Fallback to external link if not in Telegram environment
          window.open(response.data.invoice_link, '_blank');
        }
      }
    } catch (error: any) {
      console.error('Payment error:', error);
      toast.error(error.response?.data?.detail || t('paywall.error'));
    }
  };

  const handleClose = () => {
    vibrate('light');
    onClose();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 safe-area-top">
        <button
          onClick={handleClose}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          {t('paywall.close')}
        </button>
        <div className="w-16" />
      </div>

      <div className="flex-1 overflow-auto px-4 pb-28">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center">
            <Crown className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-2xl font-display font-bold text-foreground mb-2">
            {t('paywall.hero')}
          </h1>
          {feature && (
            <p className="text-muted-foreground mb-4">
              <Lock className="w-4 h-4 inline mr-1" />
              "{feature}" {t('paywall.featureOnly')}
            </p>
          )}

          {/* New Plans Table Image */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full rounded-2xl overflow-hidden border border-border shadow-xl mb-6 bg-white"
          >
            <img
              src={plansTable}
              alt="YASHA Plans"
              className="w-full h-auto object-cover"
            />
          </motion.div>
        </motion.div>

        {/* Plans */}
        <div className="space-y-4">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "relative p-5 rounded-2xl border-2 transition-all",
                plan.popular
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-4 px-3 py-1 bg-primary text-primary-foreground text-xs font-bold rounded-full flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  {t('paywall.popular')}
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-xl font-bold text-foreground mb-1">{plan.name}</h3>
                <p className="text-sm text-muted-foreground mb-3">{t(plan.descKey)}</p>
                <div className="flex items-center gap-1">
                  <span className="text-3xl font-bold text-foreground">
                    {plan.price}
                  </span>
                  <span className="text-sm text-muted-foreground">{language === 'ru' ? 'сум' : 'so\'m'}/{t(plan.periodKey)}</span>
                </div>
              </div>

              <ul className="space-y-2 mb-4">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    {feature.unlimited ? (
                      <span className="text-orange-400 flex-shrink-0">🔥</span>
                    ) : feature.limited ? (
                      <span className="text-yellow-400 flex-shrink-0">⚠️</span>
                    ) : (
                      <Check className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                    )}
                    <span className="text-foreground">{feature.text}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={plan.popular ? "hero" : "outline"}
                className="w-full"
                onClick={() => handleSubscribe(plan.id)}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                {t('paywall.subscribe')}
              </Button>
            </motion.div>
          ))}
        </div>

        {/* Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 p-4 rounded-xl bg-muted/50 border border-border"
        >
          <p className="text-sm text-muted-foreground text-center">
            {t('paywall.telegramInfo')}
          </p>
        </motion.div>

        {/* Trial notice */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center text-sm text-muted-foreground mt-4"
        >
          {t('paywall.trial')}
        </motion.p>
      </div>
    </motion.div>
  );
};

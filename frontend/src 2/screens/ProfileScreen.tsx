
import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  User, Crown, ChevronRight, LogOut,
  Bell, HelpCircle, Shield, Star, Trophy,
  Camera, Edit2, ShoppingBag, Target, Settings, BarChart3, Coins
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Paywall } from '@/components/Paywall';
import { ThemeToggle } from '@/components/ThemeToggle';
import { EditProfileSheet } from '@/components/EditProfileSheet';
import { NotificationsSheet } from '@/components/NotificationsSheet';
import { PrivacySheet } from '@/components/PrivacySheet';
import { HelpSheet } from '@/components/HelpSheet';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';
import yashaLogo from '@/assets/yasha-logo.png';

interface ProfileScreenProps {
  onNavigate?: (tab: string) => void;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ onNavigate }) => {
  const { profile, planType, premiumUntil, points, isPremium } = useUser();
  const { language, t } = useLanguage();
  const { vibrate } = useHaptic();
  const [showPaywall, setShowPaywall] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [profileImage, setProfileImage] = useState<string | null>(() => {
    return localStorage.getItem('yasha_profile_image');
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getDaysRemaining = () => {
    if (!premiumUntil) return 0;
    const now = new Date();
    const diff = premiumUntil.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  const getPlanLabel = () => {
    if (language === 'ru') {
      switch (planType?.toLowerCase()) {
        case 'pro':
        case 'vip': return '👑 PRO';
        case 'plus':
        case 'premium': return '💎 PLUS';
        case 'trial': return 'Пробный (PLUS)';
        default: return 'Бесплатный';
      }
    }
    switch (planType?.toLowerCase()) {
      case 'pro':
      case 'vip': return '👑 PRO';
      case 'plus':
      case 'premium': return '💎 PLUS';
      case 'trial': return 'Sinov (PLUS)';
      default: return 'Bepul';
    }
  };

  const getGoalLabel = () => {
    if (language === 'ru') {
      switch (profile?.goal) {
        case 'weight_loss': return 'Снижение веса';
        case 'muscle_gain': return 'Набор веса';
        case 'health': return 'Здоровый образ жизни';
        default: return 'Не указано';
      }
    }
    switch (profile?.goal) {
      case 'weight_loss': return 'Vazn yo\'qotish';
      case 'muscle_gain': return 'Vazn olish';
      case 'health': return 'Sog\'lom turmush';
      default: return 'Belgilanmagan';
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      vibrate('success');
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageData = e.target?.result as string;
        setProfileImage(imageData);
        localStorage.setItem('yasha_profile_image', imageData);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadClick = () => {
    vibrate('light');
    fileInputRef.current?.click();
  };

  const handleLogout = () => {
    vibrate('medium');
    const confirmMsg = language === 'ru' ? 'Вы хотите выйти из аккаунта?' : 'Hisobdan chiqmoqchimisiz?';
    if (confirm(confirmMsg)) {
      localStorage.clear();
      sessionStorage.clear();
      toast.success(language === 'ru' ? 'Выход выполнен' : 'Hisobdan chiqildi');
      setTimeout(() => window.location.reload(), 1000);
    }
  };

  const menuItems = [
    { icon: BarChart3, label: t('explore.reports'), action: () => { vibrate('light'); onNavigate?.('reports'); } },
    { icon: Settings, label: t('profile.settingsLang'), action: () => { vibrate('light'); onNavigate?.('settings'); } },
    { icon: Bell, label: t('profile.notifications'), action: () => { vibrate('light'); onNavigate?.('notifications'); } },
    { icon: ShoppingBag, label: language === 'ru' ? 'Магазин' : 'Do\'kon', action: () => { vibrate('light'); onNavigate?.('shop'); } },
    { icon: Shield, label: t('profile.privacy'), action: () => { vibrate('light'); setShowPrivacy(true); } },
    { icon: HelpCircle, label: t('profile.help'), action: () => { vibrate('light'); setShowHelp(true); } },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 },
  };

  const handlePremiumClick = () => {
    vibrate('medium');
    setShowPaywall(true);
  };

  // Jins label
  const getGenderLabel = () => {
    if (language === 'ru') {
      return profile?.gender === 'male' ? 'Мужской' : profile?.gender === 'female' ? 'Женский' : '—';
    }
    return profile?.gender === 'male' ? 'Erkak' : profile?.gender === 'female' ? 'Ayol' : '—';
  };

  // Translated labels
  const labels = {
    age: language === 'ru' ? 'Возраст' : 'Yosh',
    height: language === 'ru' ? 'Рост' : 'Bo\'y',
    weight: language === 'ru' ? 'Вес' : 'Vazn',
    gender: language === 'ru' ? 'Пол' : 'Jins',
    goal: language === 'ru' ? 'Цель' : 'Maqsad',
    currentPlan: language === 'ru' ? 'Текущий план' : 'Hozirgi reja',
    daysLeft: language === 'ru' ? 'дней осталось' : 'kun qoldi',
    getPremium: language === 'ru' ? 'Получить Премиум' : 'Imkoniyatlarni kengaytirish',
    yourPoints: language === 'ru' ? 'Ваши баллы' : 'Ballaringiz',
    points: language === 'ru' ? 'баллов' : 'ball',
    logout: language === 'ru' ? 'Выйти' : 'Chiqish',
    noPhone: language === 'ru' ? 'Телефон не указан' : 'Telefon raqami yo\'q',
    user: language === 'ru' ? 'Пользователь' : 'Foydalanuvchi',
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">{t('profile.title')}</h1>
          <ThemeToggle />
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-card border border-border/50 rounded-2xl p-4 mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="relative">
              <input type="file" ref={fileInputRef} onChange={handleImageUpload} accept="image/*" className="hidden" />
              <button onClick={handleUploadClick} className="w-18 h-18 rounded-2xl bg-primary/20 flex items-center justify-center overflow-hidden border-2 border-primary/30 hover:border-primary transition-colors" style={{ width: '72px', height: '72px' }}>
                {profileImage ? <img src={profileImage} alt="Profil" className="w-full h-full object-cover" /> : <User className="w-8 h-8 text-primary" />}
              </button>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg bg-primary flex items-center justify-center"><Camera className="w-3.5 h-3.5 text-primary-foreground" /></div>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold text-foreground truncate">{profile?.name || labels.user}</h2>
              <p className="text-sm text-muted-foreground truncate">{profile?.phone || labels.noPhone}</p>
            </div>
            <button
              onClick={() => { vibrate('light'); setShowEditProfile(true); }}
              className="p-2 rounded-full hover:bg-muted/50 transition-colors"
            >
              <Edit2 className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="flex items-center gap-2 p-2 rounded-xl bg-muted/50">
              <span className="text-base font-bold text-foreground">{profile?.age || 0}</span>
              <span className="text-xs text-muted-foreground">{labels.age}</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded-xl bg-muted/50">
              <span className="text-base font-bold text-foreground">{profile?.height || 0}</span>
              <span className="text-xs text-muted-foreground">{labels.height} (cm)</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded-xl bg-muted/50">
              <span className="text-base font-bold text-foreground">{profile?.weight || 0}</span>
              <span className="text-xs text-muted-foreground">{labels.weight} (kg)</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded-xl bg-muted/50">
              <span className="text-base font-bold text-foreground">{getGenderLabel()}</span>
              <span className="text-xs text-muted-foreground">{labels.gender}</span>
            </div>
          </div>
          <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{labels.goal}:</span>
              <span className="text-sm font-semibold text-primary">{getGoalLabel()}</span>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className={`rounded-2xl p-4 mb-4 ${isPremium() ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30' : 'bg-card border border-border/50'} `}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${isPremium() ? 'bg-emerald-500/20' : 'bg-muted'} `}>
                <Crown className={`w-6 h-6 ${isPremium() ? 'text-emerald-500' : 'text-muted-foreground'} `} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{labels.currentPlan}</p>
                <p className="text-lg font-bold text-foreground">{getPlanLabel()}</p>
              </div>
            </div>
            {isPremium() && (
              <div className="text-right">
                <p className="text-2xl font-bold text-emerald-500 leading-none">{getDaysRemaining()}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{labels.daysLeft}</p>
              </div>
            )}
          </div>
          {!isPremium() && <Button variant="hero" className="w-full mt-4" onClick={handlePremiumClick}><Crown className="w-5 h-5 mr-1" />{labels.getPremium}</Button>}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-card border border-border/50 rounded-2xl p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <Coins className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{language === 'ru' ? 'Ваш баланс' : 'Sizning balansingiz'}</p>
                <p className="text-base font-bold text-foreground">{points} Yasha Coin</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate?.('shop')}
              className="bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
            >
              {language === 'ru' ? 'Потратить' : 'Ishlatish'}
            </button>
          </div>
        </motion.div>

        <motion.div variants={containerVariants} initial="hidden" animate="show" className="bg-card border border-border/50 rounded-2xl overflow-hidden">
          {menuItems.map((item, index) => (
            <motion.button key={index} variants={itemVariants} onClick={item.action} className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b border-border/30 last:border-b-0">
              <div className="flex items-center gap-3">
                <item.icon className="w-5 h-5 text-muted-foreground shrink-0" />
                <span className="text-sm text-foreground text-left">{item.label}</span>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
            </motion.button>
          ))}
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="mt-4">
          <Button variant="ghost" className="w-full text-destructive hover:text-destructive hover:bg-destructive/10" onClick={handleLogout}>
            <LogOut className="w-5 h-5" />{labels.logout}
          </Button>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="mt-6 text-center">
          <img src={yashaLogo} alt="YASHA" className="w-10 h-10 mx-auto mb-2 opacity-50" />
          <p className="text-xs text-muted-foreground">YASHA AI v1.0.0</p>
        </motion.div>
      </div>

      <Paywall isOpen={showPaywall} onClose={() => setShowPaywall(false)} />
      <EditProfileSheet isOpen={showEditProfile} onClose={() => setShowEditProfile(false)} />
      <NotificationsSheet isOpen={showNotifications} onClose={() => setShowNotifications(false)} />
      <PrivacySheet isOpen={showPrivacy} onClose={() => setShowPrivacy(false)} />
      <HelpSheet isOpen={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  );
};
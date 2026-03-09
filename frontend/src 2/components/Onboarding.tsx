import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Phone, User, Ruler, Target, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useUser, UserProfile } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { WheelPicker } from '@/components/WheelPicker';
import { useHaptic } from '@/hooks/useHaptic';
import yashaLogo from '@/assets/yasha-logo.png';

type OnboardingStep = 'welcome' | 'phone' | 'name' | 'body' | 'goal' | 'activity' | 'allergies' | 'complete';

const steps: OnboardingStep[] = ['welcome', 'phone', 'name', 'body', 'goal', 'activity', 'allergies', 'complete'];

// Picker uchun qiymatlar
const ageValues = Array.from({ length: 83 }, (_, i) => i + 18); // 18-100
const heightValues = Array.from({ length: 81 }, (_, i) => i + 140); // 140-220
const weightValues = Array.from({ length: 121 }, (_, i) => i + 40); // 40-160

export const Onboarding: React.FC = () => {
  const { setProfile, completeOnboarding } = useUser();
  const { t, language } = useLanguage();
  const { vibrate } = useHaptic();
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
  const [formData, setFormData] = useState({
    phone: '',
    name: '',
    age: 25,
    gender: 'male' as 'male' | 'female',
    height: 170,
    weight: 70,
    goal: '' as 'weight_loss' | 'muscle_gain' | 'health' | '',
    activityLevel: '' as UserProfile['activityLevel'] | '',
    allergies: [] as string[],
  });

  const activityLevels = [
    { id: 'sedentary', labelKey: 'onboarding.activitySedentary', descKey: 'onboarding.activitySedentaryDesc' },
    { id: 'light', labelKey: 'onboarding.activityLight', descKey: 'onboarding.activityLightDesc' },
    { id: 'moderate', labelKey: 'onboarding.activityModerate', descKey: 'onboarding.activityModerateDesc' },
    { id: 'active', labelKey: 'onboarding.activityActive', descKey: 'onboarding.activityActiveDesc' },
    { id: 'athlete', labelKey: 'onboarding.activityVeryActive', descKey: 'onboarding.activityVeryActiveDesc' },
  ];

  const goals = [
    { id: 'weight_loss', labelKey: 'onboarding.goalLose', icon: '📉', descKey: 'onboarding.goalLoseDesc' },
    { id: 'muscle_gain', labelKey: 'onboarding.goalGain', icon: '📈', descKey: 'onboarding.goalGainDesc' },
    { id: 'health', labelKey: 'onboarding.goalMaintain', icon: '⚖️', descKey: 'onboarding.goalMaintainDesc' },
  ];

  const commonAllergies = [
    { id: 'dairy', key: 'onboarding.allergyDairy' },
    { id: 'nuts', key: 'onboarding.allergyNuts' },
    { id: 'eggs', key: 'onboarding.allergyEggs' },
    { id: 'gluten', key: 'onboarding.allergyGluten' },
    { id: 'seafood', key: 'onboarding.allergySeafood' },
    { id: 'soy', key: 'onboarding.allergySoy' },
  ];

  const currentIndex = steps.indexOf(currentStep);
  const progress = ((currentIndex) / (steps.length - 1)) * 100;

  // Telefon raqam validatsiyasi: +998XXXXXXXXX formatida bo'lishi kerak
  const isValidPhone = (phone: string): boolean => {
    const cleanPhone = phone.replace(/\s/g, '');
    const regex = /^\+998\d{9}$/;
    return regex.test(cleanPhone);
  };

  const formatPhoneNumber = (value: string): string => {
    // Faqat raqamlar va + belgisini qoldirish
    let cleaned = value.replace(/[^\d+]/g, '');

    // +998 bilan boshlanishini ta'minlash
    if (!cleaned.startsWith('+')) {
      if (cleaned.startsWith('998')) {
        cleaned = '+' + cleaned;
      } else if (cleaned.startsWith('8') || cleaned.startsWith('9')) {
        cleaned = '+998' + cleaned.slice(cleaned.startsWith('998') ? 3 : 0);
      } else if (cleaned.length > 0 && !cleaned.startsWith('+')) {
        cleaned = '+998' + cleaned;
      }
    }

    // Maksimum 13 belgi: +998XXXXXXXXX
    return cleaned.slice(0, 13);
  };

  const goNext = () => {
    vibrate('light');
    const nextIndex = currentIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex]);
    }
  };

  const goBack = () => {
    vibrate('light');
    const prevIndex = currentIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex]);
    }
  };

  const handleComplete = async () => {
    vibrate('success');
    const profile: UserProfile = {
      phone: formData.phone,
      name: formData.name,
      age: formData.age,
      gender: formData.gender,
      height: formData.height,
      weight: formData.weight,
      goal: formData.goal as 'weight_loss' | 'muscle_gain' | 'health',
      activityLevel: formData.activityLevel as UserProfile['activityLevel'],
      allergies: formData.allergies,
    };
    setProfile(profile);

    // Sync to Backend (Fix Persistence Bug)
    try {
      console.log("Syncing onboarding profile...");
      const payload: any = {
        full_name: profile.name,
        phone: profile.phone,
        age: Number(profile.age) || 0,
        height: Number(profile.height) || 0,
        weight: Number(profile.weight) || 0,
        gender: profile.gender,
        goal: profile.goal,
        activity_level: profile.activityLevel,
        allergies: profile.allergies.join(',')
      };

      console.log("DEBUG: Sending profile update:", payload);

      // We must await to ensure backend sets is_onboarded=True before completeOnboarding()
      const res = await axios.put('/user/profile', payload);
      console.log("DEBUG: Backend response:", res.data);

      setProfile(profile);
      completeOnboarding();
    } catch (e) {
      console.error("Onboarding sync failed:", e);
      // Even if it fails, we complete to avoid blocking user, 
      // but the auto-heal on next load will fix it if data partially saved.
      setProfile(profile);
      completeOnboarding();
    }
  };

  const toggleAllergy = (allergyId: string) => {
    vibrate('selection');
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.includes(allergyId)
        ? prev.allergies.filter(a => a !== allergyId)
        : [...prev.allergies, allergyId],
    }));
  };

  const handleGenderSelect = (gender: 'male' | 'female') => {
    vibrate('medium');
    setFormData({ ...formData, gender });
  };

  const handleGoalSelect = (goal: 'weight_loss' | 'muscle_gain' | 'health') => {
    vibrate('medium');
    setFormData({ ...formData, goal });
  };

  const handleActivitySelect = (activityLevel: UserProfile['activityLevel']) => {
    vibrate('medium');
    setFormData({ ...formData, activityLevel });
  };

  const slideVariants = {
    enter: { x: 50, opacity: 0 },
    center: { x: 0, opacity: 1 },
    exit: { x: -50, opacity: 0 },
  };

  return (
    <div className="min-h-screen bg-background flex flex-col safe-area-top safe-area-bottom">
      {/* Progress bar */}
      {currentStep !== 'welcome' && currentStep !== 'complete' && (
        <div className="px-4 pt-4">
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      {/* Back button */}
      {currentIndex > 0 && currentStep !== 'complete' && (
        <button
          onClick={goBack}
          className="absolute top-4 left-4 p-2 text-muted-foreground hover:text-foreground z-10"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
      )}

      {/* Content */}
      <div className="flex-1 flex flex-col px-6 py-8">
        <AnimatePresence mode="wait">
          {/* Welcome */}
          {currentStep === 'welcome' && (
            <motion.div
              key="welcome"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col items-center justify-center text-center"
            >
              <motion.img
                src={yashaLogo}
                alt="YASHA AI"
                className="w-32 h-32 mb-8"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
              />
              <h1 className="text-3xl font-display font-bold text-foreground mb-3">
                YASHA AI
              </h1>
              <p className="text-lg text-primary font-medium mb-2">
                {t('onboarding.slogan')}
              </p>
              <p className="text-muted-foreground max-w-xs mb-8">
                {t('onboarding.welcome')}
              </p>
              <Button variant="hero" size="xl" onClick={goNext} className="w-full max-w-xs">
                {t('onboarding.start')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Phone */}
          {currentStep === 'phone' && (
            <motion.div
              key="phone"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Phone className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.phoneTitle')}
              </h2>
              <p className="text-muted-foreground mb-8">
                {t('onboarding.phoneDesc')}
              </p>
              <Input
                type="tel"
                placeholder="+998991234567"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: formatPhoneNumber(e.target.value) })}
                className="text-lg h-14 mb-2"
              />
              {formData.phone.length > 0 && !isValidPhone(formData.phone) && (
                <p className="text-sm text-destructive mb-2">
                  {language === 'ru' ? 'Формат: +998XXXXXXXXX' : 'Format: +998XXXXXXXXX'}
                </p>
              )}
              {isValidPhone(formData.phone) && (
                <p className="text-sm text-primary mb-2">✓ {language === 'ru' ? 'Правильный формат' : 'To\'g\'ri format'}</p>
              )}
              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!isValidPhone(formData.phone)}
                className="w-full"
              >
                {t('onboarding.continue')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Name */}
          {currentStep === 'name' && (
            <motion.div
              key="name"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <User className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.nameTitle')}
              </h2>
              <p className="text-muted-foreground mb-8">
                {t('onboarding.nameDesc')}
              </p>
              <Input
                type="text"
                placeholder={t('onboarding.namePlaceholder')}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="text-lg h-14 mb-4"
              />
              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={formData.name.length < 2}
                className="w-full"
              >
                {t('onboarding.continue')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Body metrics - iOS style wheel picker */}
          {currentStep === 'body' && (
            <motion.div
              key="body"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Ruler className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.bodyTitle')}
              </h2>
              <p className="text-muted-foreground mb-6">
                {t('onboarding.bodyDesc')}
              </p>

              {/* Gender */}
              <div className="flex gap-3 mb-6">
                {[
                  { id: 'male', labelKey: 'onboarding.male', icon: '👨' },
                  { id: 'female', labelKey: 'onboarding.female', icon: '👩' },
                ].map((g) => (
                  <button
                    key={g.id}
                    onClick={() => handleGenderSelect(g.id as 'male' | 'female')}
                    className={`flex-1 p-4 rounded-xl border-2 transition-all ${formData.gender === g.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border bg-card'
                      }`}
                  >
                    <span className="text-2xl mb-1 block">{g.icon}</span>
                    <span className="font-medium text-foreground">{t(g.labelKey)}</span>
                  </button>
                ))}
              </div>

              {/* iOS Style Wheel Pickers */}
              <div className="flex-1 flex items-center justify-center">
                <div className="grid grid-cols-3 gap-4 w-full">
                  <WheelPicker
                    items={ageValues}
                    value={formData.age}
                    onChange={(val) => setFormData({ ...formData, age: val as number })}
                    label={t('onboarding.age')}
                    suffix={t('onboarding.ageSuffix')}
                  />
                  <WheelPicker
                    items={heightValues}
                    value={formData.height}
                    onChange={(val) => setFormData({ ...formData, height: val as number })}
                    label={t('onboarding.height')}
                    suffix={t('onboarding.heightSuffix')}
                  />
                  <WheelPicker
                    items={weightValues}
                    value={formData.weight}
                    onChange={(val) => setFormData({ ...formData, weight: val as number })}
                    label={t('onboarding.weight')}
                    suffix={t('onboarding.weightSuffix')}
                  />
                </div>
              </div>

              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                className="w-full mt-4"
              >
                {t('onboarding.continue')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Goal */}
          {currentStep === 'goal' && (
            <motion.div
              key="goal"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <Target className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.goalTitle')}
              </h2>
              <p className="text-muted-foreground mb-8">
                {t('onboarding.goalDesc')}
              </p>

              <div className="space-y-3">
                {goals.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => handleGoalSelect(goal.id as 'weight_loss' | 'muscle_gain' | 'health')}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${formData.goal === goal.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border bg-card'
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{goal.icon}</span>
                      <div>
                        <h3 className="font-semibold text-foreground">{t(goal.labelKey)}</h3>
                        <p className="text-sm text-muted-foreground">{t(goal.descKey)}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex-1" />
              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!formData.goal}
                className="w-full"
              >
                {t('onboarding.continue')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Activity */}
          {currentStep === 'activity' && (
            <motion.div
              key="activity"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.activityTitle')}
              </h2>
              <p className="text-muted-foreground mb-6">
                {t('onboarding.activityDesc')}
              </p>

              <div className="space-y-2 flex-1 overflow-auto">
                {activityLevels.map((level) => (
                  <button
                    key={level.id}
                    onClick={() => handleActivitySelect(level.id as UserProfile['activityLevel'])}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${formData.activityLevel === level.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border bg-card'
                      }`}
                  >
                    <h3 className="font-semibold text-foreground">{t(level.labelKey)}</h3>
                    <p className="text-sm text-muted-foreground">{t(level.descKey)}</p>
                  </button>
                ))}
              </div>

              <Button
                variant="hero"
                size="lg"
                onClick={goNext}
                disabled={!formData.activityLevel}
                className="w-full mt-4"
              >
                {t('onboarding.continue')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Allergies */}
          {currentStep === 'allergies' && (
            <motion.div
              key="allergies"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mb-6">
                <AlertCircle className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.allergyTitle')}
              </h2>
              <p className="text-muted-foreground mb-8">
                {t('onboarding.allergyDesc')}
              </p>

              <div className="flex flex-wrap gap-2 mb-6">
                {commonAllergies.map((allergy) => (
                  <button
                    key={allergy.id}
                    onClick={() => toggleAllergy(allergy.id)}
                    className={`px-4 py-2 rounded-full border-2 transition-all ${formData.allergies.includes(allergy.id)
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-card text-foreground'
                      }`}
                  >
                    {t(allergy.key)}
                  </button>
                ))}
              </div>

              <div className="flex-1" />
              <Button variant="hero" size="lg" onClick={goNext} className="w-full">
                {formData.allergies.length > 0 ? t('onboarding.continue') : t('onboarding.skip')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}

          {/* Complete */}
          {currentStep === 'complete' && (
            <motion.div
              key="complete"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="flex-1 flex flex-col items-center justify-center text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                className="w-24 h-24 rounded-full bg-primary/20 flex items-center justify-center mb-6"
              >
                <Sparkles className="w-12 h-12 text-primary" />
              </motion.div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {t('onboarding.completeTitle')}
              </h2>
              <p className="text-muted-foreground max-w-xs mb-8">
                {t('onboarding.completeDesc')}
              </p>
              <Button variant="hero" size="xl" onClick={handleComplete} className="w-full max-w-xs">
                {t('onboarding.letsStart')}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Calendar, Coffee, Apple, Moon, Cookie, Loader2, RefreshCw, ChevronRight, Check, ChefHat, Flame } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Paywall } from '@/components/Paywall';
import { DaySelector } from '@/components/DaySelector';
import { MealDetailsSheet } from '@/components/MealDetailsSheet';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import axios from 'axios';
import { toast } from 'sonner';

// axios.defaults.baseURL is set in UserContext.tsx

const getWeekDays = (t: (key: string) => string) => [
  t('day.mon'), t('day.tue'), t('day.wed'), t('day.thu'), t('day.fri'), t('day.sat'), t('day.sun')
];

// Suggested meals template for the weekly menu (Fallback)
const getSuggestedMealTemplates = (t: (key: string) => string) => ({
  breakfast: [
    { title: t('menu.breakfast'), calories: 350, items: ['2x', '1x', '1x', '1x'] },
    { title: t('menu.breakfast'), calories: 280, items: ['50g', '200ml', '1x', '1x'] },
    { title: t('menu.breakfast'), calories: 320, items: ['150g', '1x', '1x'] },
  ],
  lunch: [
    { title: t('menu.lunch'), calories: 550, items: ['150g', '120g', '1x', '1x'] },
    { title: t('menu.lunch'), calories: 480, items: ['100g', '100g', '1x'] },
    { title: t('menu.lunch'), calories: 420, items: ['150g', '1x', '1x', '1x'] },
  ],
  dinner: [
    { title: t('menu.dinner'), calories: 400, items: ['150g', '1x', '1x'] },
    { title: t('menu.dinner'), calories: 380, items: ['150g', '1x', '1x'] },
    { title: t('menu.dinner'), calories: 300, items: ['1x', '1x', '1x'] },
  ],
  snack: [
    { title: t('menu.snack'), calories: 150, items: ['200g', '1x', '1x'] },
    { title: t('menu.snack'), calories: 100, items: ['2x'] },
    { title: t('menu.snack'), calories: 180, items: ['1x', '1x', '1x'] },
  ],
});

const getMealIcon = (type: string) => {
  switch (type) {
    case 'breakfast': return <Coffee className="w-5 h-5 text-amber-400" />;
    case 'lunch': return <Apple className="w-5 h-5 text-green-400" />;
    case 'dinner': return <Moon className="w-5 h-5 text-purple-400" />;
    case 'snack': return <Cookie className="w-5 h-5 text-orange-400" />;
    default: return <Coffee className="w-5 h-5" />;
  }
};

const getMealTimeLabel = (type: string, t: (key: string) => string) => {
  switch (type) {
    case 'breakfast': return t('menu.breakfast');
    case 'lunch': return t('menu.lunch');
    case 'dinner': return t('menu.dinner');
    case 'snack': return t('menu.snack');
    default: return '';
  }
};

interface MenuScreenProps {
  onNavigate?: (tab: string) => void;
}

export const MenuScreen: React.FC<MenuScreenProps> = ({ onNavigate }) => {
  const { isPremium, getTodayMeals, getTodayCalories, profile, planType, canUseFeature, selectedDate, setSelectedDate } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();
  const [showPaywall, setShowPaywall] = useState(false);

  const [weeklyPlan, setWeeklyPlan] = useState<any[] | null>(null);
  const [textPlan, setTextPlan] = useState<string | null>(null);
  const [isLoadingPlan, setIsLoadingPlan] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState<any | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [startDate, setStartDate] = useState<string | null>(null);

  const fetchPlan = async () => {
    try {
      setIsLoadingPlan(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const res = await axios.get('/ai/meal', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.data.created_at) {
        setStartDate(res.data.created_at);
      }

      if (res.data.plan) {
        if (Array.isArray(res.data.plan)) {
          setWeeklyPlan(res.data.plan);
          setTextPlan(null);
        } else if (typeof res.data.plan === 'string') {
          setTextPlan(res.data.plan);
          setWeeklyPlan(null);
        }
      }
    } catch (e) {
      console.error("Failed to load plan", e);
    } finally {
      setIsLoadingPlan(false);
    }
  };

  const generatePlan = async () => {
    if (!canUseFeature('menu_generate')) {
      setShowPaywall(true);
      return;
    }
    try {
      setIsGenerating(true);
      const token = localStorage.getItem('token');
      // Start generation
      const res = await axios.post('/ai/meal', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.data.created_at) {
        setStartDate(res.data.created_at);
      }

      if (res.data.plan) {
        if (Array.isArray(res.data.plan)) {
          setWeeklyPlan(res.data.plan);
          setTextPlan(null);
        } else if (typeof res.data.plan === 'string') {
          setTextPlan(res.data.plan);
          setWeeklyPlan(null);
        }
        toast.success("Yangi menyu tayyor!");
      }
    } catch (e: any) {
      console.error(e);
      const msg = e.response?.data?.detail || "Xatolik yuz berdi";
      toast.error(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  const weekDays = getWeekDays(t);

  const today = new Date();
  const daysToShow = planType === 'pro' || planType === 'vip' ? 28 : 7;
  const days = Array.from({ length: daysToShow }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return {
      day: daysToShow > 7 ? `${date.getDate()}/${date.getMonth() + 1}` : weekDays[date.getDay() === 0 ? 6 : date.getDay() - 1],
      date: date.getDate(),
      isToday: i === 0,
    };
  });

  const handleDaySelect = (index: number) => {
    vibrate('light');
    if (index > 0 && !isPremium()) {
      setShowPaywall(true);
      return;
    }
    setSelectedDate(index);
  };

  // Get today's actual meals from context
  const todayMeals = getTodayMeals();
  const todayCalories = getTodayCalories();

  // Calculate daily goal based on profile
  const calculateDailyGoal = () => {
    if (!profile) return 2000;

    let bmr: number;
    if (profile.gender === 'male') {
      bmr = 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age);
    } else {
      bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age);
    }

    const activityMultipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9,
    };

    let tdee = bmr * (activityMultipliers[profile?.activityLevel] || 1.2);

    if (profile.goal === 'weight_loss') tdee -= 500;
    else if (profile.goal === 'muscle_gain') tdee += 300;

    return Math.round(tdee);
  };

  const dailyGoal = calculateDailyGoal();
  const suggestedMealTemplates = getSuggestedMealTemplates(t);

  let displayMeals: any[] = [];

  // Calculate plan offset based on start date
  let planOffset = 0;
  if (startDate) {
    const start = new Date(startDate);
    const now = new Date();
    // Reset hours to compare just dates
    start.setHours(0, 0, 0, 0);
    now.setHours(0, 0, 0, 0);
    const diffTime = Math.abs(now.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    // If start date is in past, offset is positive. 
    // Wait, diffTime is absolute. We need direction.
    // If start is before now, we proceed into the plan.
    if (start < now) {
      planOffset = diffDays;
    }
  }

  // 1. Show AI Weekly Plan (Priority)
  if (weeklyPlan && weeklyPlan.length > 0) {
    // Current viewed Day Index (relative to Today) = selectedDate
    // The actual Plan Day Index = planOffset + selectedDate + 1 (since plan is 1-based usually)
    // Actually our API returns `day: 1`, `day: 2` etc.
    // So we need to match `d.day === planOffset + selectedDate + 1`

    // Safety: if planOffset moves us beyond the plan length?
    // We can use modulo or just stop. 
    // For now, let's try direct mapping.
    const targetDay = (planOffset + selectedDate) % weeklyPlan.length + 1;

    const dailyData = weeklyPlan.find(d => d.day === targetDay);
    if (dailyData && dailyData.meals) {
      const types = ['breakfast', 'lunch', 'dinner', 'snack'];
      displayMeals = types.map(type => {
        const m = dailyData.meals[type];
        if (!m) return null;
        return {
          type,
          title: m.title,
          calories: m.calories,
          items: m.items || [],
          recipe: m.recipe,
          steps: m.steps
        };
      }).filter(Boolean);
    }
  }
  // 2. Show Logged Meals for Today (Fallback or if no AI Plan)
  else if (selectedDate === 0 && todayMeals.length > 0) {
    displayMeals = todayMeals.map(m => ({
      type: m.mealType,
      title: m.name,
      calories: m.calories,
      items: [`${m.protein}g ${t('menu.protein')}`, `${m.carbs}g ${t('menu.carbs')}`, `${m.fat}g ${t('menu.fat')}`],
    }));
  }

  const isMock = displayMeals.length === 0 && !weeklyPlan && !textPlan;

  // 3. Fallback to Mock
  if (isMock) {
    const getSuggestedMeals = (dayIndex: number) => {
      const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'] as const;
      return mealTypes.map(type => {
        const templates = suggestedMealTemplates[type];
        const template = templates[dayIndex % templates.length];
        return {
          type,
          ...template,
        };
      });
    };
    displayMeals = getSuggestedMeals(selectedDate);
  }

  const suggestedTotalCalories = displayMeals.reduce((sum, m) => sum + (m.calories || 0), 0);

  // For day 0 (today), show actual logged calories
  // For other days, show 0 (since they haven't happened yet)
  const displayTotalCalories = selectedDate === 0 ? todayCalories : 0;

  // Calculate macros from meals
  const calculateMacros = () => {
    if (selectedDate === 0 && todayMeals.length > 0) {
      const protein = todayMeals.reduce((sum, m) => sum + (m.protein || 0), 0);
      const carbs = todayMeals.reduce((sum, m) => sum + (m.carbs || 0), 0);
      const fat = todayMeals.reduce((sum, m) => sum + (m.fat || 0), 0);
      return { protein, carbs, fat };
    } else if (weeklyPlan && weeklyPlan.length > 0) {
      const dailyData = weeklyPlan.find(d => d.day === selectedDate + 1);
      if (dailyData && dailyData.meals) {
        const meals = Object.values(dailyData.meals) as any[];
        const protein = meals.reduce((sum: number, m: any) => sum + (m.protein || 0), 0);
        const carbs = meals.reduce((sum: number, m: any) => sum + (m.carbs || 0), 0);
        const fat = meals.reduce((sum: number, m: any) => sum + (m.fat || 0), 0);
        return { protein, carbs, fat };
      }
    }
    const estimatedProtein = Math.round(suggestedTotalCalories * 0.30 / 4);
    const estimatedCarbs = Math.round(suggestedTotalCalories * 0.40 / 4);
    const estimatedFat = Math.round(suggestedTotalCalories * 0.30 / 9);
    return { protein: estimatedProtein, carbs: estimatedCarbs, fat: estimatedFat };
  };

  const macros = calculateMacros();

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
    exit: { opacity: 0, transition: { duration: 0.1 } }
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 220,
        damping: 25
      }
    },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-2xl font-display font-bold text-foreground">
            {t('menu.title')}
          </h1>
          <div className="flex items-center gap-2">
            {profile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={generatePlan}
                disabled={isGenerating}
                className="h-8 w-8 p-0 sm:w-auto sm:px-3"
              >
                {canUseFeature('menu_generate') ? (
                  <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
                ) : (
                  <Lock className="w-4 h-4 text-muted-foreground" />
                )}
                <span className="sr-only sm:not-sr-only sm:ml-2 text-xs">AI</span>
              </Button>
            )}
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Calendar className="w-4 h-4" />
              <span className="hidden sm:inline">{t('menu.weekly')}</span>
            </div>
          </div>
        </div>

        {/* Day selector - unified component */}
        <div className="mb-5">
          <DaySelector
            days={days}
            selectedDay={selectedDate}
            onDaySelect={handleDaySelect}
            isPremium={isPremium()}
          />
        </div>

        {/* Calories Chart (Compact) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          onClick={() => onNavigate?.('calories')}
          className="mx-0 mb-5 p-4 rounded-xl bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/20 cursor-pointer active:scale-[0.98] transition-all"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-primary/20 rounded-lg text-primary">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground">{t('menu.dailyTotal')}</p>
                <p className="text-[10px] text-muted-foreground">{selectedDate === 0 ? t('common.today') : days[selectedDate].day}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-primary">
                {displayTotalCalories.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">/ {dailyGoal.toLocaleString()}</span>
              </p>
            </div>
          </div>
          {/* Thin Progress bar */}
          <div className="h-1.5 bg-background/50 rounded-full overflow-hidden w-full">
            <motion.div
              className={`h-full rounded-full ${displayTotalCalories > dailyGoal ? 'bg-red-400' : 'bg-primary'}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min((displayTotalCalories / dailyGoal) * 100, 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </motion.div>

        {/* Premium info */}
        {!isPremium() && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-primary/10 border border-primary/30 rounded-xl p-3 mb-4"
          >
            <p className="text-sm text-foreground">
              <Lock className="w-4 h-4 inline mr-1.5" />
              {t('menu.premiumInfo')}
            </p>
          </motion.div>
        )}

        {/* Healthy Recipes CTA */}

        {/* Meals */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="px-4 space-y-3"
        >
          <motion.div variants={itemVariants} className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {t('common.day')} {selectedDate + 1} - {selectedDate === 0 ? t('common.today') : days[selectedDate].day}
            </p>
            {selectedDate === 0 && todayMeals.length > 0 && (
              <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                {t('menu.actualData')}
              </span>
            )}
          </motion.div>

          {isLoadingPlan && !displayMeals.length ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : textPlan ? (
            <motion.div
              variants={itemVariants}
              className="p-5 rounded-xl bg-card border border-border/50 text-foreground"
            >
              <div
                className="prose prose-sm dark:prose-invert max-w-none break-words whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: textPlan.replace(/\n/g, '<br/>') }}
              />
            </motion.div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                layout
                variants={containerVariants}
                initial="hidden"
                animate="show"
                exit="exit"
                className="space-y-4"
                key={selectedDate} // Re-animate when date changes
              >
                {displayMeals.map((meal, index) => {
                  const isEaten = selectedDate === 0 && todayMeals.some(m => m.mealType === meal.type);

                  return (
                    <motion.div
                      key={`${selectedDate}-${index}`}
                      variants={itemVariants}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        if (isEaten) return;
                        if (selectedDate > 0 && !isPremium()) {
                          setShowPaywall(true);
                        } else {
                          vibrate('light');
                          setSelectedMeal({
                            ...meal,
                            mealType: meal.type
                          });
                          setIsSheetOpen(true);
                        }
                      }}
                      className={`p-4 rounded-xl bg-card border border-border/50 transition-all ${isEaten ? 'opacity-50 cursor-default' : 'cursor-pointer hover:border-primary/40'
                        } ${selectedDate > 0 && !isPremium() ? 'opacity-60' : ''}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2.5 rounded-xl bg-muted shrink-0 text-primary">
                          {isEaten ? <Check className="w-5 h-5" /> : getMealIcon(meal.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs text-muted-foreground">{getMealTimeLabel(meal.type, t)}</p>
                            <p className={`font-semibold ${isEaten ? 'text-muted-foreground' : 'text-foreground'}`}>{meal.calories} kcal</p>
                          </div>
                          <p className={`font-semibold mb-1 ${isEaten ? 'text-muted-foreground' : 'text-foreground'}`}>{meal.title}</p>
                          <p className="text-sm text-muted-foreground truncate">
                            {meal.items && meal.items.slice(0, 3).join(' • ')}
                            {meal.items && meal.items.length > 3 && ` +${meal.items.length - 3}`}
                          </p>
                        </div>
                        {isEaten ? (
                          <div className="mt-1">
                            <span className="text-[10px] font-bold text-primary uppercase tracking-wider bg-primary/10 px-2 py-0.5 rounded-full">
                              {t('common.done')}
                            </span>
                          </div>
                        ) : (selectedDate > 0 && !isPremium() ? (
                          <Lock className="w-4 h-4 text-muted-foreground shrink-0" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />
                        ))}
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            </AnimatePresence>
          )}


          {/* Healthy Recipes CTA */}
          <motion.button
            variants={itemVariants}
            onClick={() => onNavigate?.('recipes')}
            className="w-full p-4 rounded-xl bg-card border border-border/50 flex items-center justify-between group active:scale-[0.98] transition-all mb-4"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center text-green-500 group-hover:bg-green-500/20 transition-colors">
                <ChefHat className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-sm font-bold text-foreground">{t('explore.recipes')}</p>
                <p className="text-xs text-muted-foreground">{t('explore.recipesDesc')}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          </motion.button>

          {/* Tips */}
          <motion.div
            variants={itemVariants}
            className="p-4 rounded-xl bg-card border border-border/50"
          >
            <div className="flex items-start gap-3">
              <div className="text-xl">💡</div>
              <div>
                <h3 className="font-semibold text-foreground text-sm mb-1">{t('menu.tip')}</h3>
                <p className="text-sm text-muted-foreground">
                  {t('menu.tipText')}
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>

        <Paywall
          isOpen={showPaywall}
          onClose={() => setShowPaywall(false)}
          feature={t('paywall.aiMenu')}
        />

        <MealDetailsSheet
          meal={selectedMeal}
          isOpen={isSheetOpen}
          onClose={() => setIsSheetOpen(false)}
        />
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Plus, Flame, Apple, Coffee, Moon, Cookie, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DaySelector } from '@/components/DaySelector';
import { useUser, Meal } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';

interface CaloriesScreenProps {
  onBack?: () => void;
}

export const CaloriesScreen: React.FC<CaloriesScreenProps> = ({ onBack }) => {
  const { toast } = useToast();
  const { getTodayMeals, addMeal, removeMeal, profile, isPremium, selectedDate, setSelectedDate } = useUser();
  const { t } = useLanguage();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newMeal, setNewMeal] = useState({ name: '', calories: '', protein: '', carbs: '', fat: '', mealType: 'breakfast' });

  const weekDays = [t('day.mon'), t('day.tue'), t('day.wed'), t('day.thu'), t('day.fri'), t('day.sat'), t('day.sun')];
  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return { day: weekDays[date.getDay() === 0 ? 6 : date.getDay() - 1], date: date.getDate(), isToday: i === 0 };
  });

  const calculateDateStr = (index: number) => {
    const d = new Date();
    d.setDate(d.getDate() + index);
    return d.toISOString().split('T')[0];
  };

  const selectedDateStr = calculateDateStr(selectedDate);
  const meals = useUser().getMealsForDate(selectedDateStr);
  const calculateDailyGoal = () => {
    if (!profile) return 2000;
    let bmr = profile.gender === 'male' ? 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age) : 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age);
    const multipliers = { sedentary: 1.2, light: 1.375, moderate: 1.55, active: 1.725, very_active: 1.9 };
    let tdee = bmr * multipliers[profile.activityLevel];
    if (profile.goal === 'weight_loss') tdee -= 500;
    else if (profile.goal === 'muscle_gain') tdee += 300;
    return Math.round(tdee);
  };

  const dailyGoal = calculateDailyGoal();
  const totalCalories = meals.reduce((sum, meal) => sum + meal.calories, 0);
  const totalProtein = meals.reduce((sum, meal) => sum + meal.protein, 0);
  const totalCarbs = meals.reduce((sum, meal) => sum + meal.carbs, 0);
  const totalFat = meals.reduce((sum, meal) => sum + meal.fat, 0);
  const remaining = dailyGoal - totalCalories;

  const getMealIcon = (type: string) => {
    switch (type) {
      case 'breakfast': return <Coffee className="w-5 h-5 text-amber-400" />;
      case 'lunch': return <Apple className="w-5 h-5 text-green-400" />;
      case 'dinner': return <Moon className="w-5 h-5 text-purple-400" />;
      case 'snack': return <Cookie className="w-5 h-5 text-orange-400" />;
      default: return <Flame className="w-5 h-5" />;
    }
  };

  const getMealLabel = (type: string) => {
    switch (type) {
      case 'breakfast': return t('menu.breakfast');
      case 'lunch': return t('menu.lunch');
      case 'dinner': return t('menu.dinner');
      case 'snack': return t('calories.gazak');
      default: return '';
    }
  };

  const handleAddMeal = async () => {
    if (!newMeal.name || !newMeal.calories) {
      toast({ title: t('common.error'), description: t('calories.requiredFields'), variant: "destructive" });
      return;
    }
    addMeal({ name: newMeal.name, calories: Number(newMeal.calories), protein: Number(newMeal.protein) || 0, carbs: Number(newMeal.carbs) || 0, fat: Number(newMeal.fat) || 0, mealType: newMeal.mealType as Meal['mealType'] });
    toast({ title: t('calories.mealAdded'), description: `${newMeal.name} - ${newMeal.calories} kcal` });
    setIsAddOpen(false);
    setNewMeal({ name: '', calories: '', protein: '', carbs: '', fat: '', mealType: 'breakfast' });
  };

  const handleDeleteMeal = (id: string) => {
    removeMeal(id);
    toast({ title: t('calories.mealDeleted'), description: t('calories.mealDeletedDesc') });
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50"><ArrowLeft className="w-5 h-5" /></button>
            <div><h1 className="text-xl font-bold text-foreground">{t('calories.title')}</h1><p className="text-sm text-muted-foreground">{t('calories.dailyJournal')}</p></div>
          </div>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild><Button size="icon" className="rounded-xl"><Plus className="w-5 h-5" /></Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>{t('calories.addMeal')}</DialogTitle></DialogHeader>
              <div className="space-y-4 pt-4">
                <Input placeholder={t('calories.mealName')} value={newMeal.name} onChange={(e) => setNewMeal({ ...newMeal, name: e.target.value })} />
                <Select value={newMeal.mealType} onValueChange={(value) => setNewMeal({ ...newMeal, mealType: value })}>
                  <SelectTrigger><SelectValue placeholder={t('calories.mealType')} /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="breakfast">{t('menu.breakfast')}</SelectItem>
                    <SelectItem value="lunch">{t('menu.lunch')}</SelectItem>
                    <SelectItem value="dinner">{t('menu.dinner')}</SelectItem>
                    <SelectItem value="snack">{t('calories.gazak')}</SelectItem>
                  </SelectContent>
                </Select>
                <Input type="number" placeholder={`${t('calories.title')} (kcal)`} value={newMeal.calories} onChange={(e) => setNewMeal({ ...newMeal, calories: e.target.value })} />
                <div className="grid grid-cols-3 gap-2">
                  <Input type="number" placeholder={`${t('calories.protein')} (g)`} value={newMeal.protein} onChange={(e) => setNewMeal({ ...newMeal, protein: e.target.value })} />
                  <Input type="number" placeholder={`${t('calories.carbs')} (g)`} value={newMeal.carbs} onChange={(e) => setNewMeal({ ...newMeal, carbs: e.target.value })} />
                  <Input type="number" placeholder={`${t('calories.fat')} (g)`} value={newMeal.fat} onChange={(e) => setNewMeal({ ...newMeal, fat: e.target.value })} />
                </div>
                <Button className="w-full" onClick={handleAddMeal}><Plus className="w-4 h-4 mr-2" />{t('common.add')}</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="mb-5"><DaySelector days={days} selectedDay={selectedDate} onDaySelect={setSelectedDate} isPremium={isPremium()} /></div>

        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-5 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div><p className="text-sm text-muted-foreground">{selectedDate === 0 ? t('calories.todayCalories') : `${days[selectedDate].day} ${t('calories.title')}`}</p><p className="text-3xl font-bold text-foreground">{totalCalories.toLocaleString()}</p></div>
            <div className="text-right"><p className="text-sm text-muted-foreground">{t('calories.remaining')}</p><p className={`text-2xl font-bold ${remaining >= 0 ? 'text-green-400' : 'text-red-400'}`}>{remaining >= 0 ? remaining.toLocaleString() : `+${Math.abs(remaining).toLocaleString()}`}</p></div>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden mb-4"><motion.div className={`h-full rounded-full ${totalCalories > dailyGoal ? 'bg-red-400' : 'bg-primary'}`} initial={{ width: 0 }} animate={{ width: `${Math.min((totalCalories / dailyGoal) * 100, 100)}%` }} transition={{ duration: 1 }} /></div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 rounded-xl bg-card/50 border border-border/30"><p className="text-lg font-bold text-foreground">{totalProtein}g</p><p className="text-xs text-muted-foreground">{t('calories.protein')}</p></div>
            <div className="text-center p-3 rounded-xl bg-card/50 border border-border/30"><p className="text-lg font-bold text-foreground">{totalCarbs}g</p><p className="text-xs text-muted-foreground">{t('calories.carbs')}</p></div>
            <div className="text-center p-3 rounded-xl bg-card/50 border border-border/30"><p className="text-lg font-bold text-foreground">{totalFat}g</p><p className="text-xs text-muted-foreground">{t('calories.fat')}</p></div>
          </div>
        </motion.div>

        <div className="space-y-3">
          <h2 className="text-base font-bold text-foreground">{selectedDate === 0 ? t('calories.todayMeals') : `${days[selectedDate].day} ${t('calories.todayMeals').toLowerCase()}`}</h2>
          {meals.length === 0 ? (
            <div className="p-6 rounded-2xl bg-card border border-border/50 text-center"><Flame className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" /><p className="text-muted-foreground">{t('calories.noMeals')}</p><p className="text-sm text-muted-foreground/70">{t('calories.addMealHint')}</p></div>
          ) : meals.map((meal) => (
            <motion.div key={meal.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-4 rounded-2xl bg-card border border-border/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3"><div className="p-2.5 rounded-xl bg-muted">{getMealIcon(meal.mealType)}</div><div><p className="font-semibold text-foreground">{meal.name}</p><p className="text-sm text-muted-foreground">{getMealLabel(meal.mealType)}</p></div></div>
                <div className="flex items-center gap-3">
                  <div className="text-right"><p className="font-bold text-foreground">{meal.calories}</p><p className="text-xs text-muted-foreground">kcal</p></div>
                  <button onClick={() => handleDeleteMeal(meal.id)} className="p-2 text-muted-foreground hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
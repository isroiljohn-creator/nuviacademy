import React from 'react';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { Utensils, Clock, Flame, ListChecks, ChefHat, Check } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useHaptic } from '@/hooks/useHaptic';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { useState } from 'react';

interface MealDetails {
    title: string;
    calories: number;
    mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    items: string[];
    recipe?: string;
    steps?: string[];
}

interface MealDetailsSheetProps {
    meal: MealDetails | null;
    isOpen: boolean;
    onClose: () => void;
}

export const MealDetailsSheet: React.FC<MealDetailsSheetProps> = ({
    meal,
    isOpen,
    onClose,
}) => {
    const { t } = useLanguage();
    const { addMeal } = useUser();
    const { vibrate } = useHaptic();
    const [isAdding, setIsAdding] = useState(false);
    const [isAdded, setIsAdded] = useState(false);

    if (!meal) return null;

    const handleAteClick = async () => {
        try {
            setIsAdding(true);
            vibrate('medium');

            await addMeal({
                name: meal.title,
                calories: meal.calories,
                mealType: meal.mealType,
                protein: 0,
                carbs: 0,
                fat: 0
            });

            setIsAdded(true);
            toast.success(t('menu.mealAddedSuccess'));
            vibrate('success');

            // Close after a short delay
            setTimeout(() => {
                onClose();
                setIsAdded(false);
            }, 800);
        } catch (error) {
            console.error("Failed to add meal", error);
            toast.error(t('common.error'));
        } finally {
            setIsAdding(false);
        }
    };

    return (
        <Sheet open={isOpen} onOpenChange={onClose}>
            <SheetContent side="bottom" className="h-[85vh] rounded-t-[32px] bg-card border-t-border/50 p-0 overflow-hidden">
                <div className="h-1.5 w-12 bg-muted rounded-full mx-auto mt-3 mb-1" />

                <div className="overflow-y-auto h-full pb-10 px-6">
                    <SheetHeader className="text-left py-4">
                        <SheetTitle className="text-2xl font-bold flex items-center gap-2">
                            <Utensils className="w-6 h-6 text-primary" />
                            {meal.title}
                        </SheetTitle>
                        <div className="flex items-center gap-4 mt-2">
                            <div className="flex items-center gap-1.5 text-primary bg-primary/10 px-3 py-1 rounded-full text-sm font-semibold">
                                <Flame className="w-4 h-4" />
                                {meal.calories} kkal
                            </div>
                        </div>
                    </SheetHeader>

                    <div className="space-y-6 mt-4">
                        {/* Ingredients Section */}
                        <section className="space-y-3">
                            <div className="flex items-center gap-2 text-lg font-bold text-foreground">
                                <ListChecks className="w-5 h-5 text-primary" />
                                {t('recipes.ingredients')}
                            </div>
                            <div className="grid grid-cols-1 gap-2">
                                {meal.items.map((item, idx) => (
                                    <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-muted/30 border border-border/50">
                                        <div className="w-2 h-2 rounded-full bg-primary/50" />
                                        <span className="text-sm font-medium">{item}</span>
                                    </div>
                                ))}
                            </div>
                        </section>

                        {/* Recipe Info Section */}
                        {meal.recipe && (
                            <section className="space-y-3">
                                <div className="flex items-center gap-2 text-lg font-bold text-foreground">
                                    <ChefHat className="w-5 h-5 text-primary" />
                                    {t('menu.tip')}
                                </div>
                                <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 text-sm leading-relaxed">
                                    {meal.recipe}
                                </div>
                            </section>
                        )}

                        {/* Steps Section */}
                        {meal.steps && meal.steps.length > 0 && (
                            <section className="space-y-4">
                                <div className="text-lg font-bold text-foreground mb-4">
                                    {t('recipes.preparation')}
                                </div>
                                <div className="space-y-4">
                                    {meal.steps.map((step, idx) => (
                                        <div key={idx} className="flex gap-4">
                                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1 pt-1.5 text-sm leading-relaxed text-muted-foreground">
                                                {step}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}
                    </div>
                </div>

                {/* Fixed Footer with Button */}
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-card via-card to-transparent pt-10">
                    <Button
                        size="lg"
                        className="w-full text-lg h-14 rounded-2xl shadow-lg shadow-primary/20 transition-all active:scale-[0.98]"
                        onClick={handleAteClick}
                        disabled={isAdding || isAdded}
                    >
                        {isAdded ? (
                            <><Check className="mr-2 h-6 w-6" /> {t('common.done')}</>
                        ) : (
                            <><Flame className="mr-2 h-6 w-6" /> {t('menu.iAteIt')}</>
                        )}
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    );
};

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChefHat, Clock, Flame, X, Users, ArrowLeft } from 'lucide-react';
import { useHaptic } from '@/hooks/useHaptic';
import { useLanguage } from '@/contexts/LanguageContext';

interface Recipe {
  id: string;
  nameUz: string;
  nameRu: string;
  image: string;
  calories: number;
  timeUz: string;
  timeRu: string;
  servings: number;
  categoryUz: string;
  categoryRu: string;
  ingredientsUz: string[];
  ingredientsRu: string[];
  stepsUz: string[];
  stepsRu: string[];
}

const recipes: Recipe[] = [
  {
    id: '1',
    nameUz: 'Protein salat',
    nameRu: 'Протеиновый салат',
    image: '🥗',
    calories: 350,
    timeUz: '15 daq',
    timeRu: '15 мин',
    servings: 1,
    categoryUz: 'Nonushta',
    categoryRu: 'Завтрак',
    ingredientsUz: ['2 ta tuxum', '100g tovuq', '1 ta pomidor', '1 ta bodring', 'Salat barglari', 'Zaytun moyi'],
    ingredientsRu: ['2 яйца', '100г курицы', '1 помидор', '1 огурец', 'Листья салата', 'Оливковое масло'],
    stepsUz: ['Tuxumlarni qaynatib maydalang', 'Tovuqni pishirib bo\'laklang', 'Sabzavotlarni to\'g\'rang', 'Hammasini aralashtiring'],
    stepsRu: ['Отварите и нарежьте яйца', 'Обжарьте и нарежьте курицу', 'Нарежьте овощи', 'Всё перемешайте']
  },
  {
    id: '2',
    nameUz: 'Oatmeal smoothie',
    nameRu: 'Овсяный смузи',
    image: '🥤',
    calories: 280,
    timeUz: '5 daq',
    timeRu: '5 мин',
    servings: 1,
    categoryUz: 'Nonushta',
    categoryRu: 'Завтрак',
    ingredientsUz: ['50g jo\'xori', '1 ta banan', '200ml sut', '1 osh qoshiq asal'],
    ingredientsRu: ['50г овсянки', '1 банан', '200мл молока', '1 ст.л. мёда'],
    stepsUz: ['Barcha ingredientlarni blenderga soling', '1-2 daqiqa aralashtiring', 'Stakanga quying'],
    stepsRu: ['Поместите все ингредиенты в блендер', 'Смешивайте 1-2 минуты', 'Налейте в стакан']
  },
  {
    id: '3',
    nameUz: 'Tovuqli palov',
    nameRu: 'Плов с курицей',
    image: '🍚',
    calories: 550,
    timeUz: '45 daq',
    timeRu: '45 мин',
    servings: 2,
    categoryUz: 'Tushlik',
    categoryRu: 'Обед',
    ingredientsUz: ['200g guruch', '150g tovuq', '1 ta sabzi', '1 ta piyoz', 'Ziravorlar'],
    ingredientsRu: ['200г риса', '150г курицы', '1 морковь', '1 луковица', 'Специи'],
    stepsUz: ['Piyozni halqa qilib to\'g\'rang', 'Sabzini uzun qilib to\'g\'rang', 'Moyda piyozni qizarting', 'Tovuqni qo\'shib pishiring', 'Guruch va suv qo\'shib 30 daqiqa pishiring'],
    stepsRu: ['Нарежьте лук кольцами', 'Нарежьте морковь соломкой', 'Обжарьте лук в масле', 'Добавьте курицу и обжарьте', 'Добавьте рис и воду, готовьте 30 минут']
  },
  {
    id: '4',
    nameUz: 'Grechka bilan baliq',
    nameRu: 'Гречка с рыбой',
    image: '🐟',
    calories: 420,
    timeUz: '30 daq',
    timeRu: '30 мин',
    servings: 1,
    categoryUz: 'Kechki ovqat',
    categoryRu: 'Ужин',
    ingredientsUz: ['150g baliq', '100g grechka', 'Limon', 'Tuz, qora murch'],
    ingredientsRu: ['150г рыбы', '100г гречки', 'Лимон', 'Соль, перец'],
    stepsUz: ['Grechkani suv bilan pishiring', 'Baliqni tuzlang', '180°C da 20 daqiqa pishiring'],
    stepsRu: ['Сварите гречку', 'Посолите рыбу', 'Запекайте при 180°C 20 минут']
  },
  {
    id: '5',
    nameUz: 'Yogurt parfait',
    nameRu: 'Йогурт парфе',
    image: '🍨',
    calories: 180,
    timeUz: '5 daq',
    timeRu: '5 мин',
    servings: 1,
    categoryUz: 'Yengil taom',
    categoryRu: 'Перекус',
    ingredientsUz: ['200g yogurt', '50g granola', 'Mevalar', '1 choy qoshiq asal'],
    ingredientsRu: ['200г йогурта', '50г гранолы', 'Фрукты', '1 ч.л. мёда'],
    stepsUz: ['Stakanga yogurt qo\'ying', 'Granola qatlamini qo\'shing', 'Mevalarni ustiga joylashtiring'],
    stepsRu: ['Положите йогурт в стакан', 'Добавьте слой гранолы', 'Сверху положите фрукты']
  }
];

interface RecipesScreenProps {
  onBack?: () => void;
}

export const RecipesScreen: React.FC<RecipesScreenProps> = ({ onBack }) => {
  const { vibrate } = useHaptic();
  const { language, t } = useLanguage();
  const [selectedCategoryKey, setSelectedCategoryKey] = useState('all');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  const categories = [
    { key: 'all', uz: 'Hammasi', ru: 'Все' },
    { key: 'breakfast', uz: 'Nonushta', ru: 'Завтрак' },
    { key: 'lunch', uz: 'Tushlik', ru: 'Обед' },
    { key: 'dinner', uz: 'Kechki ovqat', ru: 'Ужин' },
    { key: 'snack', uz: 'Yengil taom', ru: 'Перекус' },
  ];

  const getCategoryLabel = (cat: typeof categories[0]) => language === 'ru' ? cat.ru : cat.uz;

  const filteredRecipes = selectedCategoryKey === 'all' 
    ? recipes 
    : recipes.filter(r => {
        const catMap: Record<string, string> = { breakfast: 'Nonushta', lunch: 'Tushlik', dinner: 'Kechki ovqat', snack: 'Yengil taom' };
        return r.categoryUz === catMap[selectedCategoryKey];
      });

  const getRecipeName = (r: Recipe) => language === 'ru' ? r.nameRu : r.nameUz;
  const getRecipeCategory = (r: Recipe) => language === 'ru' ? r.categoryRu : r.categoryUz;
  const getRecipeTime = (r: Recipe) => language === 'ru' ? r.timeRu : r.timeUz;
  const getRecipeIngredients = (r: Recipe) => language === 'ru' ? r.ingredientsRu : r.ingredientsUz;
  const getRecipeSteps = (r: Recipe) => language === 'ru' ? r.stepsRu : r.stepsUz;

  const openRecipe = (recipe: Recipe) => { vibrate('medium'); setSelectedRecipe(recipe); };
  const closeRecipe = () => { vibrate('light'); setSelectedRecipe(null); };

  const labels = {
    title: language === 'ru' ? 'Рецепты' : 'Retseptlar',
    subtitle: language === 'ru' ? 'Здоровые блюда' : 'Sog\'lom taomlar',
    kcal: language === 'ru' ? 'ккал' : 'kkal',
    time: language === 'ru' ? 'время' : 'vaqt',
    servings: language === 'ru' ? 'порций' : 'porsiya',
    ingredients: language === 'ru' ? 'Ингредиенты' : 'Ingredientlar',
    preparation: language === 'ru' ? 'Приготовление' : 'Tayyorlash',
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-5">
          {onBack && (
            <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-foreground">{labels.title}</h1>
            <p className="text-sm text-muted-foreground">{labels.subtitle}</p>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
          {categories.map((cat) => (
            <button
              key={cat.key}
              onClick={() => { vibrate('light'); setSelectedCategoryKey(cat.key); }}
              className={`px-3 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                selectedCategoryKey === cat.key
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-card border border-border/50 text-foreground'
              }`}
            >
              {getCategoryLabel(cat)}
            </button>
          ))}
        </div>
      </div>

      <motion.div layout className="px-4 grid grid-cols-2 gap-3">
        <AnimatePresence>
          {filteredRecipes.map((recipe) => (
            <motion.div
              key={recipe.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => openRecipe(recipe)}
              className="p-4 rounded-2xl bg-card border border-border/50 cursor-pointer"
            >
              <div className="text-4xl mb-3">{recipe.image}</div>
              <h3 className="font-semibold text-foreground text-sm mb-2 truncate">{getRecipeName(recipe)}</h3>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-1"><Flame className="w-3.5 h-3.5" />{recipe.calories}</div>
                <div className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{getRecipeTime(recipe)}</div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {selectedRecipe && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/50 z-50 flex items-end" onClick={closeRecipe}>
            <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ type: 'spring', damping: 25 }} onClick={(e) => e.stopPropagation()} className="w-full max-h-[85vh] bg-background rounded-t-3xl overflow-hidden">
              <div className="w-12 h-1 bg-muted rounded-full mx-auto mt-3" />
              <div className="p-5 overflow-y-auto max-h-[80vh]">
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-4">
                    <div className="text-5xl">{selectedRecipe.image}</div>
                    <div>
                      <h2 className="text-xl font-bold text-foreground">{getRecipeName(selectedRecipe)}</h2>
                      <p className="text-sm text-muted-foreground">{getRecipeCategory(selectedRecipe)}</p>
                    </div>
                  </div>
                  <button onClick={closeRecipe} className="p-2 text-muted-foreground"><X className="w-6 h-6" /></button>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-5">
                  <div className="p-3 rounded-xl bg-card border border-border/50 text-center">
                    <Flame className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                    <p className="text-sm font-bold text-foreground">{selectedRecipe.calories}</p>
                    <p className="text-xs text-muted-foreground">{labels.kcal}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-card border border-border/50 text-center">
                    <Clock className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                    <p className="text-sm font-bold text-foreground">{getRecipeTime(selectedRecipe)}</p>
                    <p className="text-xs text-muted-foreground">{labels.time}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-card border border-border/50 text-center">
                    <Users className="w-5 h-5 text-primary mx-auto mb-1" />
                    <p className="text-sm font-bold text-foreground">{selectedRecipe.servings}</p>
                    <p className="text-xs text-muted-foreground">{labels.servings}</p>
                  </div>
                </div>

                <div className="mb-5">
                  <h3 className="font-bold text-foreground mb-3">{labels.ingredients}</h3>
                  <div className="space-y-2">
                    {getRecipeIngredients(selectedRecipe).map((ing, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                        <span className="text-sm text-foreground">{ing}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-bold text-foreground mb-3">{labels.preparation}</h3>
                  <div className="space-y-3">
                    {getRecipeSteps(selectedRecipe).map((step, i) => (
                      <div key={i} className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-primary/20 text-primary text-sm font-bold flex items-center justify-center shrink-0">{i + 1}</div>
                        <p className="text-sm text-foreground">{step}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
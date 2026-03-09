import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
axios.defaults.baseURL = API_URL;

export interface UserProfile {
  phone: string;
  name: string;
  age: number;
  gender: 'male' | 'female';
  height: number;
  weight: number;
  goal: 'weight_loss' | 'muscle_gain' | 'health';
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'athlete';
  allergies: string[];
}

export interface Meal {
  id: string;
  name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  date: string;
}

export interface WorkoutLog {
  id: string;
  name: string;
  duration: number;
  caloriesBurned: number;
  date: string;
}

export interface DailyLog {
  date: string;
  water_ml: number;
  steps: number;
  sleep_hours: number;
  mood: 'bad' | 'ok' | 'good';
  calories_consumed: number;
  workout_done: boolean;
}

export type PlanType = 'free' | 'plus' | 'pro' | 'trial' | 'premium' | 'vip';

interface UserState {
  isOnboarded: boolean;
  profile: UserProfile | null;
  planType: PlanType;
  premiumUntil: Date | null;
  trialUsed: boolean;
  points: number;
  elixir: number;
  streaks: {
    water: number;
    sleep: number;
    mood: number;
    workout: number;
  };
  todayLog: DailyLog | null;
  meals: Meal[];
  workouts: WorkoutLog[];
  notificationSettings: {
    waterReminders: boolean;
    waterInterval: string;
    workoutReminders: boolean;
    workoutTime: string;
    sleepReminders: boolean;
    sleepTime: string;
  };
  language: 'uz' | 'ru';
  entitlements: any | null;
}

interface UserContextType extends UserState {
  setProfile: (profile: UserProfile) => void;
  completeOnboarding: () => void;
  updateTodayLog: (log: Partial<DailyLog>) => void;
  addWater: (ml: number) => void;
  isPremium: () => boolean;
  checkAndDowngrade: () => boolean;
  canUseFeature: (feature: string) => boolean;
  getFeatureStatus: (feature: string) => any;
  // Meals management
  addMeal: (meal: Omit<Meal, 'id' | 'date'>) => void;
  removeMeal: (id: string) => void;
  getTodayMeals: () => Meal[];
  getMealsForDate: (date: string) => Meal[];
  getTodayCalories: () => number;
  getCaloriesForDate: (date: string) => number;
  // Workouts management
  addWorkout: (workout: Omit<WorkoutLog, 'id' | 'date'>) => void;
  getTodayWorkouts: () => WorkoutLog[];
  getWorkoutsForDate: (date: string) => WorkoutLog[];
  markWorkoutDone: () => void;
  resetData: () => Promise<void>;
  updateNotificationSettings: (settings: Partial<UserState['notificationSettings']>) => Promise<void>;
  updateLanguage: (lang: 'uz' | 'ru') => Promise<void>;
  isLoading: boolean;
  selectedDate: number; // Index of the selected day (0-6 or more)
  setSelectedDate: (date: number) => void;
}


const UserContext = createContext<UserContextType | undefined>(undefined);

const getTodayDate = () => new Date().toISOString().split('T')[0];

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<UserState>(() => {
    const saved = localStorage.getItem('yasha_user');
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        ...parsed,
        premiumUntil: parsed.premiumUntil ? new Date(parsed.premiumUntil) : null,
        meals: parsed.meals || [],
        workouts: parsed.workouts || [],
        points: parsed.points || 0,
        elixir: parsed.elixir || 0,
        streaks: {
          water: parsed.streaks?.water || 0,
          sleep: parsed.streaks?.sleep || 0,
          mood: parsed.streaks?.mood || 0,
          workout: parsed.streaks?.workout || 0,
        },
      };
    }
    return {
      isOnboarded: false,
      profile: null,
      planType: 'free' as PlanType,
      premiumUntil: null,
      trialUsed: false,
      points: 0,
      elixir: 0,
      streaks: { water: 0, sleep: 0, mood: 0, workout: 0 },
      todayLog: null,
      meals: [],
      workouts: [],
      notificationSettings: {
        waterReminders: true,
        waterInterval: '2',
        workoutReminders: true,
        workoutTime: '09:00',
        sleepReminders: true,
        sleepTime: '22:00',
      },
      language: 'uz',
      entitlements: null,
    };
  });

  const token = localStorage.getItem('token');
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  const [isLoading, setIsLoading] = useState(true); // Start as loading by default! 
  const [selectedDate, setSelectedDate] = useState(0);

  // Axios Interceptor for 401 Auto-Refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Attempt re-auth with Telegram initData
            const tg = (window as any).Telegram?.WebApp;
            if (tg?.initData) {
              console.log("🔄 401 Detected! Auto-refreshing token via initData...");

              // Call login directly (bypass full initializeUser for speed)
              const authRes = await axios.post('/auth/telegram', {
                initData: tg.initData
              });

              if (authRes.data.token) {
                const newToken = authRes.data.token;
                localStorage.setItem('token', newToken);
                axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                console.log("✅ Token Refreshed! Retrying original request.");
                return axios(originalRequest);
              }
            }
          } catch (refreshError) {
            console.error("❌ Token Refresh Failed:", refreshError);
            // If refresh fails, we might want to logout or just let it fail
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, []);

  useEffect(() => {
    const initializeUser = async () => {
      try {
        const tg = (window as any).Telegram?.WebApp;
        if (tg?.initData) {
          console.log("Authenticating with Telegram initData...");
          const authRes = await axios.post('/auth/telegram', {
            initData: tg.initData
          });

          if (authRes.data.token) {
            const token = authRes.data.token;
            localStorage.setItem('token', token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

            // Fetch profile AND entitlements in parallel
            const [profileRes, entRes] = await Promise.all([
              axios.get('/user/profile'),
              axios.get('/user/entitlements').catch(e => ({ data: null }))
            ]);

            const userData = profileRes.data;
            const entitlements = entRes.data || null;

            console.log("DEBUG: Initial User Profile Fetched:", userData);
            console.log("DEBUG: Entitlements:", entitlements);

            // Construct new state from backend data mapping snake_case to camelCase
            const profile: UserProfile = {
              phone: userData.phone || '',
              name: userData.full_name || userData.username || 'Foydalanuvchi',
              age: userData.age || 0,
              gender: userData.gender as 'male' | 'female',
              height: userData.height || 0,
              weight: userData.weight || 0,
              goal: (userData.goal as 'weight_loss' | 'muscle_gain' | 'health') || 'weight_loss',
              activityLevel: (userData.activity_level as any) || 'sedentary',
              allergies: userData.allergies ? String(userData.allergies).split(',') : [],
            };

            // Trust backend is_onboarded flag, but fallback to our logic if it is false (e.g. legacy users)
            const isOnboarded = !!(userData.is_onboarded || (
              profile.age > 0 ||
              profile.weight > 0 ||
              profile.name !== 'Foydalanuvchi' ||
              profile.phone
            ));
            console.log("DEBUG: Determined isOnboarded:", isOnboarded);

            setState(prev => {
              // Merge with previous state to keep streaks/logs if valuable?
              // But usually backend logic rules.
              // Let's assume backend is source of truth for Plan/Points too.

              const newState: UserState = {
                ...prev,
                isOnboarded: isOnboarded,
                profile: profile,
                // Prefer entitlements plan if available, else profile plan
                planType: (entitlements?.plan || userData.plan_type || 'free').toLowerCase() as PlanType,
                premiumUntil: userData.premium_until ? new Date(userData.premium_until) : null,
                points: userData.points || 0,
                elixir: userData.elixir || 0, // Fetch from backend
                entitlements: entitlements,
                // Streaks from backend
                streaks: {
                  ...prev.streaks,
                  water: userData.streak_water || 0,
                  sleep: userData.streak_sleep || 0,
                  mood: userData.streak_mood || 0,
                  workout: userData.streak_workout || 0,
                },
                // trialUsed from backend? Not in profile response explicitly but handled via planType logic usually
                // Backend profile has "plan_type"

                // Sync Today's Log
                todayLog: {
                  ...prev.todayLog,
                  date: getTodayDate(),
                  water_ml: userData.today_water || 0,
                  steps: userData.today_steps || 0,
                  sleep_hours: userData.today_sleep || 0,
                  // calories/workout status might need separate sync or included in profile stats
                  calories_consumed: prev.todayLog?.calories_consumed || 0,
                  workout_done: prev.todayLog?.workout_done || false,
                  mood: prev.todayLog?.mood || 'ok'
                } as DailyLog,
                language: userData.language || 'uz',
                notificationSettings: userData.notification_settings || prev.notificationSettings
              };

              localStorage.setItem('yasha_user', JSON.stringify(newState));
              return newState;
            });
          }
        }
      } catch (error) {
        console.error("Auth Error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeUser();
  }, []);

  const saveState = useCallback((newState: UserState) => {
    localStorage.setItem('yasha_user', JSON.stringify(newState));
    setState(newState);
  }, []);

  const updateNotificationSettings = useCallback(async (newSettings: Partial<UserState['notificationSettings']>) => {
    const updatedSettings = { ...state.notificationSettings, ...newSettings };
    setState(prev => ({ ...prev, notificationSettings: updatedSettings }));

    try {
      await axios.put('/user/profile', {
        notification_settings: updatedSettings
      });
    } catch (e) {
      console.error("Sync notification settings failed", e);
    }
  }, [state.notificationSettings]);

  const updateLanguage = useCallback(async (lang: 'uz' | 'ru') => {
    setState(prev => ({ ...prev, language: lang }));
    localStorage.setItem('yasha_language', lang); // Also sync with LanguageContext's local storage key

    try {
      await axios.put('/user/profile', {
        language: lang
      });
    } catch (e) {
      console.error("Sync language failed", e);
    }
  }, []);

  const setProfile = useCallback((profile: UserProfile) => {
    const newState = { ...state, profile };
    saveState(newState);
  }, [state, saveState]);

  const completeOnboarding = useCallback(() => {
    const premiumUntil = new Date();
    premiumUntil.setDate(premiumUntil.getDate() + 7);

    const newState: UserState = {
      ...state,
      isOnboarded: true,
      planType: (state.planType || 'trial').toLowerCase() as PlanType,
      premiumUntil,
      trialUsed: true,
      todayLog: {
        date: getTodayDate(),
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok',
        calories_consumed: 0,
        workout_done: false,
      },
    };
    saveState(newState);
  }, [state, saveState]);

  const updateTodayLog = useCallback((log: Partial<DailyLog>) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newLog = { ...currentLog, ...log };
    const newState = { ...state, todayLog: newLog };
    saveState(newState);
  }, [state, saveState]);

  const addWater = useCallback(async (ml: number) => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newWater = currentLog.water_ml + ml;
    const wasCompleted = currentLog.water_ml >= 2500;
    const isNowCompleted = newWater >= 2500;

    let newPoints = state.points;
    let newStreaks = { ...state.streaks };

    if (!wasCompleted && isNowCompleted) {
      newPoints += 20; // 20 XP for goal
      newStreaks.water += 1;
    } else {
      newPoints += 2; // 2 XP per glass
    }

    const newState = {
      ...state,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, water_ml: newWater },
    };
    saveState(newState);

    try {
      await axios.post('/entry/water', { amount: ml });
    } catch (e) {
      console.error("Sync water failed", e);
    }
  }, [state, saveState]);

  // Meals management
  const addMeal = useCallback(async (meal: Omit<Meal, 'id' | 'date'>) => {
    const today = getTodayDate();
    const newMeal: Meal = {
      ...meal,
      id: Date.now().toString(),
      date: today,
    };

    const newMeals = [...state.meals, newMeal];
    const todayMeals = newMeals.filter(m => m.date === today);
    const totalCalories = todayMeals.reduce((sum, m) => sum + m.calories, 0);

    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newState = {
      ...state,
      points: state.points + 5, // 5 XP per meal logged
      meals: newMeals,
      todayLog: { ...currentLog, calories_consumed: totalCalories },
    };
    saveState(newState);

    try {
      await axios.post('/entry/meals', {
        name: meal.name,
        calories: meal.calories,
        protein: meal.protein,
        carbs: meal.carbs,
        fat: meal.fat,
        meal_type: meal.mealType,
        date: today
      });
    } catch (e) {
      console.error("Sync meal failed", e);
    }
  }, [state, saveState]);

  const removeMeal = useCallback((id: string) => {
    // Sync removal is tricky as backend might rely on ID? 
    // Backend API doesn't support DELETE yet. 
    // Skipping sync for removal for MVP or add TODO.
    const today = getTodayDate();
    const newMeals = state.meals.filter(m => m.id !== id);
    const todayMeals = newMeals.filter(m => m.date === today);
    const totalCalories = todayMeals.reduce((sum, m) => sum + m.calories, 0);

    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    const newState = {
      ...state,
      meals: newMeals,
      todayLog: { ...currentLog, calories_consumed: totalCalories },
    };
    saveState(newState);
  }, [state, saveState]);

  const getTodayMeals = useCallback(() => {
    const today = getTodayDate();
    return state.meals.filter(m => m.date === today);
  }, [state.meals]);

  const getMealsForDate = useCallback((date: string) => {
    return state.meals.filter(m => m.date === date);
  }, [state.meals]);

  const getTodayCalories = useCallback(() => {
    const today = getTodayDate();
    return state.meals
      .filter(m => m.date === today)
      .reduce((sum, m) => sum + m.calories, 0);
  }, [state.meals]);

  const getCaloriesForDate = useCallback((date: string) => {
    return state.meals
      .filter(m => m.date === date)
      .reduce((sum, m) => sum + m.calories, 0);
  }, [state.meals]);

  // Workouts management
  const addWorkout = useCallback(async (workout: Omit<WorkoutLog, 'id' | 'date'>) => {
    const today = getTodayDate();
    const newWorkout: WorkoutLog = {
      ...workout,
      id: Date.now().toString(),
      date: today,
    };

    const newWorkouts = [...state.workouts, newWorkout];

    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    let newPoints = state.points + 50; // 50 XP per workout session
    let newStreaks = { ...state.streaks };

    if (!currentLog.workout_done) {
      newStreaks.workout += 1;
    }

    const newState = {
      ...state,
      workouts: newWorkouts,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, workout_done: true },
    };
    saveState(newState);

    try {
      await axios.post('/entry/workouts', {
        name: workout.name,
        duration: workout.duration,
        calories_burned: workout.caloriesBurned,
        date: today
      });
    } catch (e) {
      console.error("Sync workout failed", e);
    }
  }, [state, saveState]);

  const getTodayWorkouts = useCallback(() => {
    const today = getTodayDate();
    return state.workouts.filter(w => w.date === today);
  }, [state.workouts]);

  const getWorkoutsForDate = useCallback((date: string) => {
    return state.workouts.filter(w => w.date === date);
  }, [state.workouts]);

  const markWorkoutDone = useCallback(() => {
    const today = getTodayDate();
    const currentLog = state.todayLog?.date === today
      ? state.todayLog
      : {
        date: today,
        water_ml: 0,
        steps: 0,
        sleep_hours: 0,
        mood: 'ok' as const,
        calories_consumed: 0,
        workout_done: false,
      };

    if (currentLog.workout_done) return;

    let newPoints = state.points + 50; // 50 XP per workout session
    let newStreaks = { ...state.streaks };
    newStreaks.workout += 1;

    const newState = {
      ...state,
      points: newPoints,
      streaks: newStreaks,
      todayLog: { ...currentLog, workout_done: true },
    };
    saveState(newState);
  }, [state, saveState]);

  const isPremium = useCallback(() => {
    const type = state.planType?.toLowerCase();
    return type === 'plus' || type === 'pro' || type === 'premium' || type === 'vip' || type === 'trial';
  }, [state.planType]);

  const canUseFeature = useCallback((feature: string) => {
    if (state.entitlements && state.entitlements.features) {
      const feat = state.entitlements.features[feature];
      if (!feat) return false;

      if (feat.limit === null) return true; // Unlimited
      if (feat.remaining !== undefined) return feat.remaining > 0;
      if (feat.limit === 0) return false;
    }

    // Fallback
    const isPrem = isPremium();
    if (feature === 'menu_generate' || feature === 'workout_generate') return isPrem;
    return true;
  }, [state.entitlements, isPremium]);

  const getFeatureStatus = useCallback((feature: string) => {
    if (state.entitlements && state.entitlements.features) {
      return state.entitlements.features[feature] || null;
    }
    return null;
  }, [state.entitlements]);

  const checkAndDowngrade = useCallback(() => {
    if (state.planType !== 'free' && state.premiumUntil && new Date() >= state.premiumUntil) {
      const newState = { ...state, planType: 'free' as PlanType };
      saveState(newState);
      return true;
    }
    return false;
    return false;
  }, [state, saveState]);

  const resetData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await axios.post('/user/reset');
      }
    } catch (e) {
      console.error("Reset failed", e);
    } finally {
      localStorage.clear();
      // Optional: don't reload immediately if caller handles it, but implementation plan said reload.
      // Actually PrivacySheet handles reload. 
      // UserContext should just reset state.

      const resetState: UserState = {
        isOnboarded: false,
        profile: null,
        planType: 'free',
        premiumUntil: null,
        trialUsed: false,
        points: 0,
        elixir: 0,
        entitlements: null,
        streaks: { water: 0, sleep: 0, mood: 0, workout: 0 },
        todayLog: null,
        meals: [],
        workouts: [],
        notificationSettings: {
          waterReminders: true,
          waterInterval: '2',
          workoutReminders: true,
          workoutTime: '09:00',
          sleepReminders: true,
          sleepTime: '22:00',
        },
        language: 'uz',
      };
      saveState(resetState);
    }
  }, [saveState]);

  return (
    <UserContext.Provider
      value={{
        ...state,
        setProfile,
        completeOnboarding,
        updateTodayLog,
        addWater,
        isPremium,
        canUseFeature,
        getFeatureStatus,
        checkAndDowngrade,
        addMeal,
        removeMeal,
        getTodayMeals,
        getMealsForDate,
        getTodayCalories,
        getCaloriesForDate,
        addWorkout,
        getTodayWorkouts,
        getWorkoutsForDate,
        markWorkoutDone,
        resetData,
        updateNotificationSettings,
        updateLanguage,
        isLoading,
        selectedDate,
        setSelectedDate,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
};

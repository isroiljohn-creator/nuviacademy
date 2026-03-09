import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Onboarding } from '@/components/Onboarding';
import { BottomNavigation } from '@/components/BottomNavigation';
import { SplashScreen } from '@/components/SplashScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { MenuScreen } from '@/screens/MenuScreen';
import { WorkoutScreen } from '@/screens/WorkoutScreen';
import { HabitsScreen } from '@/screens/HabitsScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { AiCoachScreen } from '@/screens/AiCoachScreen';
import { WeightScreen } from '@/screens/WeightScreen';
import { AchievementsScreen } from '@/screens/AchievementsScreen';
import { MeditationScreen } from '@/screens/MeditationScreen';
import { RecipesScreen } from '@/screens/RecipesScreen';
import { ReportsScreen } from '@/screens/ReportsScreen';
import { FriendsScreen } from '@/screens/FriendsScreen';
import { ChallengesScreen } from '@/screens/ChallengesScreen';
import { ReferralsScreen } from '@/screens/ReferralsScreen';
import { CaloriesScreen } from '@/screens/CaloriesScreen';
import { WorkoutLibraryScreen } from '@/screens/WorkoutLibraryScreen';
import { DailyTasksScreen } from '@/screens/DailyTasksScreen';
import { ShopScreen } from '@/screens/ShopScreen';
import { NotificationSettingsScreen } from '@/screens/NotificationSettingsScreen';
import { ExploreScreen } from '@/screens/ExploreScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import { UserProvider, useUser } from '@/contexts/UserContext';
import { LanguageProvider } from '@/contexts/LanguageContext';

const AppContent: React.FC = () => {
  const { isOnboarded, isLoading } = useUser();
  const [activeTab, setActiveTab] = useState('home');
  const [showSplash, setShowSplash] = useState(true);

  // Deep linking support via ?tab=...
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab) {
      setActiveTab(tab);
    }
  }, [window.location.search]);

  useEffect(() => {
    // Splash faqat bir marta ko'rsatiladi (kuniga bir marta)
    const lastSplashDate = localStorage.getItem('yasha_splash_date');
    const today = new Date().toISOString().split('T')[0];

    if (lastSplashDate === today) {
      setShowSplash(false);
    }
  }, []);

  const handleSplashComplete = () => {
    const today = new Date().toISOString().split('T')[0];
    localStorage.setItem('yasha_splash_date', today);
    setShowSplash(false);
  };

  if (showSplash) {
    return <SplashScreen onComplete={handleSplashComplete} />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isOnboarded) {
    return <Onboarding />;
  }

  const renderScreen = () => {
    switch (activeTab) {
      case 'home': return <HomeScreen onNavigate={setActiveTab} />;
      case 'menu': return <MenuScreen onNavigate={setActiveTab} />;
      case 'workout': return <WorkoutScreen onNavigate={setActiveTab} />;
      case 'habits': return <HabitsScreen />;
      case 'profile': return <ProfileScreen onNavigate={setActiveTab} />;
      case 'ai-coach': return <AiCoachScreen />;
      case 'weight': return <WeightScreen onBack={() => setActiveTab('home')} />;
      case 'achievements': return <AchievementsScreen onBack={() => setActiveTab('home')} />;
      case 'meditation': return <MeditationScreen onBack={() => setActiveTab('home')} />;
      case 'recipes': return <RecipesScreen />;
      case 'reports': return <ReportsScreen onBack={() => setActiveTab('profile')} />;
      case 'friends': return <FriendsScreen onBack={() => setActiveTab('home')} />;
      case 'challenges': return <ChallengesScreen onBack={() => setActiveTab('home')} />;
      case 'referrals': return <ReferralsScreen onBack={() => setActiveTab('home')} />;
      case 'calories': return <CaloriesScreen onBack={() => setActiveTab('home')} />;
      case 'workout-library': return <WorkoutLibraryScreen onBack={() => setActiveTab('home')} />;
      case 'daily-tasks': return <DailyTasksScreen onBack={() => setActiveTab('home')} />;
      case 'shop': return <ShopScreen onBack={() => setActiveTab('profile')} />;
      case 'notifications': return <NotificationSettingsScreen onBack={() => setActiveTab('profile')} />;
      case 'explore': return <ExploreScreen onNavigate={setActiveTab} onBack={() => setActiveTab('home')} />;
      case 'settings': return <SettingsScreen onBack={() => setActiveTab('profile')} />;
      default: return <HomeScreen onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="w-full"
        >
          {renderScreen()}
        </motion.div>
      </AnimatePresence>
      <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};

const Index: React.FC = () => {
  return (
    <UserProvider>
      <LanguageProvider>
        <AppContent />
      </LanguageProvider>
    </UserProvider>
  );
};

export default Index;

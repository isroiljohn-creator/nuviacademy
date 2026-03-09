// Haptic Feedback Hook for Telegram Mini App
export const useHaptic = () => {
  const vibrate = (pattern: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'selection' = 'light') => {
    // 1. Try Telegram WebApp API
    const tg = (window as any).Telegram?.WebApp;

    if (tg?.HapticFeedback) {
      try {
        switch (pattern) {
          case 'light':
            tg.HapticFeedback.impactOccurred('light');
            break;
          case 'medium':
            tg.HapticFeedback.impactOccurred('medium');
            break;
          case 'heavy':
            tg.HapticFeedback.impactOccurred('heavy');
            break;
          case 'success':
            tg.HapticFeedback.notificationOccurred('success');
            break;
          case 'error':
            tg.HapticFeedback.notificationOccurred('error');
            break;
          case 'selection':
            tg.HapticFeedback.selectionChanged();
            break;
        }
        return; // Success
      } catch (e) {
        console.warn('Telegram Haptic Error:', e);
      }
    }

    // 2. Fallback to Browser Vibration API (for development/testing)
    if (navigator.vibrate) {
      const patterns: Record<string, number | number[]> = {
        light: 10,
        medium: 25,
        heavy: 50,
        success: [10, 50, 10],
        error: [50, 30, 50],
        selection: 5
      };
      // Short vibration for simple feedbacks
      navigator.vibrate(patterns[pattern] || 10);
    }
  };

  return { vibrate };
};

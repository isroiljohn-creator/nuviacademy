import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import yashaLogo from '@/assets/yasha-logo.png';
import { useHaptic } from '@/hooks/useHaptic';

interface SplashScreenProps {
  onComplete: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [showLogo, setShowLogo] = useState(false);
  const { vibrate } = useHaptic();

  useEffect(() => {
    // Logo paydo bo'lishida vibratsiya
    const logoTimer = setTimeout(() => {
      setShowLogo(true);
      vibrate('medium');
    }, 10);

    // Uchib chiqish animatsiyasida vibratsiya
    const flyTimer = setTimeout(() => {
      vibrate('success');
    }, 400);

    // Splash tugashi
    const completeTimer = setTimeout(() => {
      vibrate('light');
      onComplete();
    }, 800);

    return () => {
      clearTimeout(logoTimer);
      clearTimeout(flyTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete, vibrate]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] bg-background flex flex-col items-center justify-center"
      >
        {/* Glow effect */}
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1.5, opacity: 0.3 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="absolute w-64 h-64 rounded-full bg-primary blur-3xl"
        />

        {/* Logo - qush uchib chiqadi */}
        <motion.div
          initial={{ y: 100, opacity: 0, scale: 0.5, rotate: -15 }}
          animate={showLogo ? {
            y: [100, -20, 0],
            opacity: 1,
            scale: [0.5, 1.2, 1],
            rotate: [-15, 10, 0]
          } : {}}
          transition={{
            duration: 0.4,
            ease: "easeOut",
            times: [0, 0.6, 1]
          }}
          className="relative z-10"
        >
          <motion.img
            src={yashaLogo}
            alt="YASHA AI"
            className="w-32 h-32"
            animate={showLogo ? {
              y: [0, -8, 0],
            } : {}}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.4
            }}
          />
        </motion.div>

        {/* Matn */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.3 }}
          className="mt-8 text-center"
        >
          <h1 className="text-4xl font-display font-bold text-foreground mb-2">
            YASHA AI
          </h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-lg text-primary font-medium"
          >
            Sog'lom hayot murabbiyi
          </motion.p>
        </motion.div>

        {/* Loading dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="absolute bottom-20 flex gap-2"
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-primary"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

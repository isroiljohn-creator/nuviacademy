import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Coins, ShoppingBag, Check, Lock, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';

interface ShopItem {
  id: string;
  nameKey: string;
  descKey: string;
  itemType: 'avatar' | 'badge' | 'theme' | 'boost';
  priceCoins: number;
  purchased: boolean;
}

interface ShopScreenProps {
  onBack?: () => void;
}

export const ShopScreen: React.FC<ShopScreenProps> = ({ onBack }) => {
  const { t } = useLanguage();
  const { toast } = useToast();
  const { points } = useUser(); // Connect to real points
  const [userCoins, setUserCoins] = useState(points); // Initialize with real points, though ideally use points directly
  // Note: userCoins is used for immediate UI feedback in this screen's local logic for now.
  // Better approach: use points directly and handle specific purchase sync later.
  // For the bug fix: Sync start state.

  React.useEffect(() => {
    setUserCoins(points);
  }, [points]);

  const [activeTab, setActiveTab] = useState('all');

  const [items, setItems] = useState<ShopItem[]>([
    { id: '1', nameKey: 'shop.goldenFrame', descKey: 'shop.goldenFrameDesc', itemType: 'avatar', priceCoins: 100, purchased: false },
    { id: '2', nameKey: 'shop.darkTheme', descKey: 'shop.darkThemeDesc', itemType: 'theme', priceCoins: 200, purchased: true },
    { id: '3', nameKey: 'shop.xpBoost', descKey: 'shop.xpBoostDesc', itemType: 'boost', priceCoins: 150, purchased: false },
    { id: '4', nameKey: 'shop.championBadge', descKey: 'shop.championBadgeDesc', itemType: 'badge', priceCoins: 300, purchased: false },
    { id: '5', nameKey: 'shop.silverFrame', descKey: 'shop.silverFrameDesc', itemType: 'avatar', priceCoins: 50, purchased: true },
    { id: '6', nameKey: 'shop.colorTheme', descKey: 'shop.colorThemeDesc', itemType: 'theme', priceCoins: 180, purchased: false },
    { id: '7', nameKey: 'shop.starBadge', descKey: 'shop.starBadgeDesc', itemType: 'badge', priceCoins: 250, purchased: false },
    { id: '8', nameKey: 'shop.coinBoost', descKey: 'shop.coinBoostDesc', itemType: 'boost', priceCoins: 200, purchased: false },
  ]);

  const getItemTypeIcon = (type: string) => {
    switch (type) {
      case 'avatar': return '🖼️';
      case 'badge': return '🏆';
      case 'theme': return '🎨';
      case 'boost': return '⚡';
      default: return '✨';
    }
  };

  const getItemTypeBorder = (type: string) => {
    switch (type) {
      case 'avatar': return 'border-purple-500/30';
      case 'badge': return 'border-amber-500/30';
      case 'theme': return 'border-blue-500/30';
      case 'boost': return 'border-green-500/30';
      default: return 'border-primary/30';
    }
  };

  const filteredItems = activeTab === 'all'
    ? items
    : items.filter(item => item.itemType === activeTab);

  const handlePurchase = (itemId: string) => {
    const item = items.find(i => i.id === itemId);
    if (!item) return;

    if (item.purchased) {
      toast({
        title: t('shop.alreadyOwned'),
        description: t('shop.alreadyOwnedDesc'),
        variant: "destructive",
      });
      return;
    }

    if (userCoins < item.priceCoins) {
      toast({
        title: t('shop.notEnough'),
        description: `${t('shop.notEnoughDesc')}: ${item.priceCoins}`,
        variant: "destructive",
      });
      return;
    }

    setUserCoins(prev => prev - item.priceCoins);
    setItems(items.map(i =>
      i.id === itemId ? { ...i, purchased: true } : i
    ));

    toast({
      title: `${t('shop.success')} 🎉`,
      description: `${t(item.nameKey)} ${t('shop.purchased')}`,
    });
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1 },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="p-2.5 rounded-xl bg-card border border-border/50">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-foreground">{t('shop.title')}</h1>
              <p className="text-sm text-muted-foreground">{t('shop.subtitle')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-amber-500/20 px-4 py-2.5 rounded-xl border border-amber-500/30">
            <Coins className="w-5 h-5 text-amber-400" />
            <span className="text-lg font-bold text-amber-400">{userCoins}</span>
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full h-12 p-1 bg-card border border-border/50">
            <TabsTrigger value="all" className="flex-1 text-sm">{t('shop.all')}</TabsTrigger>
            <TabsTrigger value="avatar" className="flex-1 text-sm">{t('shop.frames')}</TabsTrigger>
            <TabsTrigger value="theme" className="flex-1 text-sm">{t('shop.themes')}</TabsTrigger>
            <TabsTrigger value="boost" className="flex-1 text-sm">{t('shop.boosts')}</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-4">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="grid grid-cols-2 gap-3"
            >
              {filteredItems.map((item) => {
                const canAfford = userCoins >= item.priceCoins;

                return (
                  <motion.div
                    key={item.id}
                    variants={itemVariants}
                    className={`p-4 rounded-2xl bg-card border-2 ${getItemTypeBorder(item.itemType)} relative`}
                  >
                    {/* Purchased badge */}
                    {item.purchased && (
                      <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                        <Check className="w-4 h-4 text-white" />
                      </div>
                    )}

                    {/* Icon */}
                    <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mb-3 text-2xl">
                      {getItemTypeIcon(item.itemType)}
                    </div>

                    {/* Content */}
                    <h3 className="font-semibold text-foreground text-sm mb-1 line-clamp-1">{t(item.nameKey)}</h3>
                    <p className="text-xs text-muted-foreground mb-4 line-clamp-2 min-h-[32px]">{t(item.descKey)}</p>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <Coins className="w-4 h-4 text-amber-400" />
                        <span className="font-bold text-foreground">{item.priceCoins}</span>
                      </div>

                      {item.purchased ? (
                        <span className="text-xs text-green-400 font-medium px-2 py-1 bg-green-500/10 rounded-lg">{t('shop.owned')}</span>
                      ) : (
                        <Button
                          size="sm"
                          variant={canAfford ? "default" : "outline"}
                          disabled={!canAfford}
                          onClick={() => handlePurchase(item.id)}
                          className="h-8 px-3 text-xs"
                        >
                          {canAfford ? t('shop.buy') : <Lock className="w-3.5 h-3.5" />}
                        </Button>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

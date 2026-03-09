import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useUser, UserProfile } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useHaptic } from '@/hooks/useHaptic';
import { toast } from 'sonner';

interface EditProfileSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EditProfileSheet: React.FC<EditProfileSheetProps> = ({ isOpen, onClose }) => {
  const { profile, setProfile } = useUser();
  const { t } = useLanguage();
  const { vibrate } = useHaptic();

  const [formData, setFormData] = useState({
    name: profile?.name || '',
    phone: profile?.phone || '',
    age: profile?.age || 0,
    height: profile?.height || 0,
    weight: profile?.weight || 0,
  });

  if (!isOpen) return null;

  const handleSave = () => {
    vibrate('success');
    if (profile) {
      setProfile({
        ...profile,
        name: formData.name,
        phone: formData.phone,
        age: formData.age,
        height: formData.height,
        weight: formData.weight,
      });
    }
    toast.success(t('editProfile.saved'));
    onClose();
  };

  const handleClose = () => {
    vibrate('light');
    onClose();
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm overflow-auto"
      >
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between p-4 border-b border-border bg-background/80 backdrop-blur-lg safe-area-top z-10">
          <button onClick={handleClose} className="text-muted-foreground">
            <X className="w-6 h-6" />
          </button>
          <h2 className="text-lg font-bold text-foreground">{t('editProfile.title')}</h2>
          <Button size="sm" onClick={handleSave}>
            <Save className="w-4 h-4 mr-1" />
            {t('editProfile.save')}
          </Button>
        </div>

        <div className="p-4 pb-28 space-y-4">
          {/* Name */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">{t('editProfile.name')}</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder={t('editProfile.namePlaceholder')}
              className="h-12"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">{t('editProfile.phone')}</label>
            <Input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="+998 90 123 45 67"
              className="h-12"
            />
          </div>

          {/* Age */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">{t('editProfile.age')}</label>
            <Input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 0 })}
              placeholder="25"
              className="h-12"
            />
          </div>

          {/* Height */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">{t('editProfile.height')}</label>
            <Input
              type="number"
              value={formData.height}
              onChange={(e) => setFormData({ ...formData, height: parseInt(e.target.value) || 0 })}
              placeholder="170"
              className="h-12"
            />
          </div>

          {/* Weight */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">{t('editProfile.weight')}</label>
            <Input
              type="number"
              value={formData.weight}
              onChange={(e) => setFormData({ ...formData, weight: parseInt(e.target.value) || 0 })}
              placeholder="70"
              className="h-12"
            />
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

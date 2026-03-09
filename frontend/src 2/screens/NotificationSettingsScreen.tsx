import React, { useState } from 'react';
import { useUser } from '@/contexts/UserContext';
import { motion } from 'framer-motion';
import { ArrowLeft, Bell, Droplets, Dumbbell, Moon, Clock, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';

interface NotificationSettingsScreenProps {
  onBack?: () => void;
}

export const NotificationSettingsScreen: React.FC<NotificationSettingsScreenProps> = ({ onBack }) => {
  const { toast } = useToast();
  const { notificationSettings, updateNotificationSettings } = useUser();

  const [localSettings, setLocalSettings] = useState(notificationSettings || {
    waterReminders: false,
    waterInterval: '2',
    workoutReminders: false,
    workoutTime: '07:00',
    sleepReminders: false,
    sleepTime: '22:00'
  });

  const handleSave = async () => {
    try {
      await updateNotificationSettings(localSettings);
      toast({
        title: "Saqlandi!",
        description: "Eslatma sozlamalari muvaffaqiyatli saqlandi",
      });
    } catch (error) {
      toast({
        title: "Xatolik!",
        description: "Sozlamalarni saqlashda xatolik yuz berdi",
        variant: "destructive",
      });
    }
  };

  const updateSetting = (key: string, value: any) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2 rounded-full bg-card">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-foreground">Eslatmalar</h1>
            <p className="text-sm text-muted-foreground">Bildirishnoma sozlamalari</p>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {/* Water Reminders */}
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Droplets className="w-6 h-6 text-blue-400" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground">Suv ichish eslatmasi</p>
                <p className="text-sm text-muted-foreground">Muntazam suv ichishni eslatadi</p>
              </div>
              <Switch
                checked={localSettings.waterReminders}
                onCheckedChange={(checked) => updateSetting('waterReminders', checked)}
              />
            </div>

            {localSettings.waterReminders && (
              <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>Har necha soatda</span>
                </div>
                <Select
                  value={localSettings.waterInterval}
                  onValueChange={(value) => updateSetting('waterInterval', value)}
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 soat</SelectItem>
                    <SelectItem value="2">2 soat</SelectItem>
                    <SelectItem value="3">3 soat</SelectItem>
                    <SelectItem value="4">4 soat</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Workout Reminders */}
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                <Dumbbell className="w-6 h-6 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground">Mashq eslatmasi</p>
                <p className="text-sm text-muted-foreground">Kunlik mashq qilishni eslatadi</p>
              </div>
              <Switch
                checked={localSettings.workoutReminders}
                onCheckedChange={(checked) => updateSetting('workoutReminders', checked)}
              />
            </div>

            {localSettings.workoutReminders && (
              <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>Eslatma vaqti</span>
                </div>
                <Select
                  value={localSettings.workoutTime}
                  onValueChange={(value) => updateSetting('workoutTime', value)}
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="06:00">06:00</SelectItem>
                    <SelectItem value="07:00">07:00</SelectItem>
                    <SelectItem value="08:00">08:00</SelectItem>
                    <SelectItem value="09:00">09:00</SelectItem>
                    <SelectItem value="17:00">17:00</SelectItem>
                    <SelectItem value="18:00">18:00</SelectItem>
                    <SelectItem value="19:00">19:00</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Sleep Reminders */}
          <div className="p-4 rounded-2xl bg-card border border-border/50">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                <Moon className="w-6 h-6 text-indigo-400" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground">Uyqu eslatmasi</p>
                <p className="text-sm text-muted-foreground">Uxlash vaqti ekanligini eslatadi</p>
              </div>
              <Switch
                checked={localSettings.sleepReminders}
                onCheckedChange={(checked) => updateSetting('sleepReminders', checked)}
              />
            </div>

            {localSettings.sleepReminders && (
              <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>Uyqu vaqti</span>
                </div>
                <Select
                  value={localSettings.sleepTime}
                  onValueChange={(value) => updateSetting('sleepTime', value)}
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="21:00">21:00</SelectItem>
                    <SelectItem value="22:00">22:00</SelectItem>
                    <SelectItem value="23:00">23:00</SelectItem>
                    <SelectItem value="00:00">00:00</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="p-4 rounded-2xl bg-primary/10 border border-primary/30">
            <div className="flex items-start gap-3">
              <Bell className="w-5 h-5 text-primary mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Eslatma haqida</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Eslatmalar faqat ilova ochiq bo'lganda ishlaydi. Tizimli bildirishnomalar uchun qurilmangiz sozlamalaridan ruxsat bering.
                </p>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <Button className="w-full" size="lg" onClick={handleSave}>
            <Save className="w-5 h-5 mr-2" />
            Saqlash
          </Button>
        </motion.div>
      </div>
    </div>
  );
};

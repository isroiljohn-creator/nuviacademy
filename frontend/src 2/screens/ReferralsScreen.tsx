import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Users, Copy, Check, Gift, ArrowLeft } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';

interface ReferralUser {
    id: number;
    name: string;
    date: string;
    points: number;
}

interface ReferralData {
    code: string;
    link: string;
    total_invited: number;
    total_earned: number;
    referrals: ReferralUser[];
}

interface ReferralsScreenProps {
    onBack?: () => void;
}

export const ReferralsScreen: React.FC<ReferralsScreenProps> = ({ onBack }) => {
    const { t } = useLanguage();
    const { toast } = useToast();
    const [data, setData] = useState<ReferralData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchReferrals();
    }, []);

    const fetchReferrals = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/referrals`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (typeof res.data === 'string' || !res.data.referrals) {
                throw new Error("Invalid API response");
            }

            setData(res.data);
        } catch (error) {
            console.error(error);
            toast({
                title: "Xatolik",
                description: "Ma'lumotlarni yuklashda xatolik",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    const copyLink = () => {
        if (data?.link) {
            navigator.clipboard.writeText(data.link);
            setCopied(true);
            toast({
                title: "Nusxalandi",
                description: "Havola buferga saqlandi",
            });
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="min-h-screen bg-background pb-28">
            {/* Header */}
            <div className="px-4 pt-5 pb-3 safe-area-top">
                <div className="flex items-center gap-3 mb-6">
                    <button onClick={onBack} className="p-2.5 rounded-full bg-card border border-border/50">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-foreground">Referallar</h1>
                        <p className="text-sm text-muted-foreground">Do'stlarni taklif qiling</p>
                    </div>
                </div>

                {isLoading ? (
                    <div className="flex justify-center p-10">
                        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : (
                    <div className="space-y-6">

                        {/* Stats Card */}
                        <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center">
                                    <Gift className="w-6 h-6 text-indigo-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Jami ishlangan</p>
                                    <p className="text-2xl font-bold text-foreground">{data?.total_earned} coin</p>
                                </div>
                            </div>
                            <div className="flex items-center justify-between text-sm pt-4 border-t border-indigo-500/20">
                                <span className="text-muted-foreground">Taklif qilinganlar:</span>
                                <span className="font-semibold text-foreground">{data?.total_invited} ta</span>
                            </div>
                        </div>

                        {/* Link Section */}
                        <div className="p-5 rounded-2xl bg-card border border-border">
                            <h3 className="text-sm font-medium text-muted-foreground mb-3">Sizning havolangiz</h3>
                            <div className="flex items-center gap-2 p-3 bg-secondary/50 rounded-xl mb-3">
                                <p className="text-sm font-mono text-foreground flex-1 truncate">{data?.link}</p>
                                <Button size="icon" variant="ghost" onClick={copyLink}>
                                    {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                                </Button>
                            </div>
                            <p className="text-xs text-muted-foreground text-center">
                                Do'stingiz ro'yxatdan o'tsa +1 coin olasiz!
                            </p>
                        </div>

                        {/* Friends List */}
                        <div>
                            <h3 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
                                <Users className="w-4 h-4" /> Mening do'stlarim
                            </h3>

                            <div className="space-y-3">
                                {data && data.referrals.length > 0 ? (
                                    data.referrals.map((user) => (
                                        <motion.div
                                            key={user.id}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="p-4 rounded-xl bg-card border border-border flex items-center justify-between"
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                                                    {user.name.charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-foreground">{user.name}</p>
                                                    <p className="text-xs text-muted-foreground">{user.date}</p>
                                                </div>
                                            </div>
                                            <div className="px-2 py-1 rounded-lg bg-green-500/10 text-green-500 text-xs font-bold">
                                                +{user.points} coin
                                            </div>
                                        </motion.div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground text-sm">
                                        Hali hech kimni taklif qilmadingiz.
                                    </div>
                                )}
                            </div>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
};

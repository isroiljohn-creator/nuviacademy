import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { Loader2, Save, Gift } from "lucide-react";

interface AdminSetting {
    key: string;
    value: string;
    updated_at: string;
}

export default function Settings() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [rewardValue, setRewardValue] = useState<string>("");

    const { data: settings, isLoading } = useQuery<AdminSetting[]>({
        queryKey: ["admin_settings"],
        queryFn: () => fetchApi("/api/admin/settings"),
    });

    useEffect(() => {
        if (settings) {
            const reward = settings.find(s => s.key === "reward_amount");
            if (reward) setRewardValue(reward.value);
        }
    }, [settings]);

    const mutation = useMutation({
        mutationFn: (value: string) =>
            fetchApi("/api/admin/settings/reward_amount", {
                method: "PUT",
                body: JSON.stringify({ value })
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin_settings"] });
            toast({
                title: "Muvaffaqiyatli saqlandi",
                description: "Referal mukofoti yangilandi.",
            });
        },
        onError: () => {
            toast({
                variant: "destructive",
                title: "Xatolik",
                description: "Sozlamani saqlashda xatolik yuz berdi.",
            });
        }
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12 text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Yuklanmoqda...
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <h2 className="text-base font-bold">Tizim Sozlamalari</h2>

            <Card className="glass-card border-border/30">
                <CardHeader className="p-4 pb-2">
                    <div className="flex items-center gap-2">
                        <Gift className="h-5 w-5 text-primary" />
                        <CardTitle className="text-sm">Referal Dasturi</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="p-4 pt-0 space-y-4">
                    <div className="space-y-2">
                        <label className="text-xs text-muted-foreground font-medium">
                            Har bir taklif uchun mukofot (so'm)
                        </label>
                        <div className="flex gap-2">
                            <Input
                                type="number"
                                value={rewardValue}
                                onChange={(e) => setRewardValue(e.target.value)}
                                placeholder="20000"
                                className="bg-secondary border-border/30 text-sm h-10"
                            />
                            <Button
                                onClick={() => mutation.mutate(rewardValue)}
                                disabled={mutation.isPending}
                                className="h-10 px-4"
                            >
                                {mutation.isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Save className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                        <p className="text-[10px] text-muted-foreground italic">
                            * Bu qiymat botdagi matnlarda va hisob-kitoblarda avtomatik yangilanadi.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

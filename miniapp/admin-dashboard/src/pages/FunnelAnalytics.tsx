import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface FunnelStep {
  label: string;
  users: number;
  rate: number;
}

export default function FunnelAnalytics() {
  const { data: funnelData, isLoading } = useQuery<FunnelStep[]>({
    queryKey: ["admin_funnel"],
    queryFn: () => fetchApi("/api/admin/funnel"),
  });

  const funnelSteps = funnelData || [];
  const maxUsers = funnelSteps.length > 0 ? funnelSteps[0].users : 1;

  // Calculate conversion and drop-off dynamically
  const totalConversion = funnelSteps.length >= 2
    ? ((funnelSteps[funnelSteps.length - 1].users / funnelSteps[0].users) * 100).toFixed(1)
    : "0";

  // Find the biggest drop-off step
  let biggestDropLabel = "—";
  let biggestDrop = 0;
  for (let i = 1; i < funnelSteps.length; i++) {
    const drop = funnelSteps[i - 1].users - funnelSteps[i].users;
    if (drop > biggestDrop) {
      biggestDrop = drop;
      biggestDropLabel = `${funnelSteps[i - 1].label} → ${funnelSteps[i].label}`;
    }
  }

  // Find the best conversion step
  let bestStepLabel = "—";
  let bestRate = 0;
  for (let i = 1; i < funnelSteps.length; i++) {
    const rate = funnelSteps[i - 1].users > 0
      ? (funnelSteps[i].users / funnelSteps[i - 1].users) * 100
      : 0;
    if (rate > bestRate) {
      bestRate = rate;
      bestStepLabel = `${funnelSteps[i - 1].label} → ${funnelSteps[i].label}`;
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold">Voronka analitikasi</h2>
        <button className="px-3 py-1.5 text-[11px] font-medium bg-secondary text-secondary-foreground rounded-md">
          Hozirgi holat
        </button>
      </div>

      <Card className="glass-card border-border/30">
        <CardContent className="p-4 space-y-3">
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-4">Yuklanmoqda...</div>
          ) : funnelSteps.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Ma'lumot topilmadi</div>
          ) : (
            funnelSteps.map((step, i) => {
              const widthPct = (step.users / maxUsers) * 100;
              const dropoff = i > 0
                ? (((funnelSteps[i - 1].users - step.users) / funnelSteps[i - 1].users) * 100).toFixed(1)
                : null;

              return (
                <div key={step.label}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium">{step.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold">{step.users.toLocaleString()}</span>
                      {dropoff && (
                        <span className="text-[10px] text-destructive font-medium">
                          −{dropoff}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="h-7 bg-secondary rounded-md overflow-hidden relative">
                    <div
                      className="h-full rounded-md transition-all duration-700"
                      style={{
                        width: `${widthPct}%`,
                        background: `linear-gradient(90deg, hsl(199, 85%, 55%), hsl(199, 85%, ${45 + i * 4}%))`,
                      }}
                    />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground">
                      {i > 0 ? `${step.rate}%` : ""}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Umumiy konversiya", value: `${totalConversion}%` },
          { label: "Eng katta yo'qotish", value: biggestDropLabel },
          { label: "Eng yaxshi bosqich", value: bestStepLabel },
        ].map((s) => (
          <Card key={s.label} className="glass-card border-border/30">
            <CardContent className="p-3 text-center">
              <p className="text-sm font-bold text-primary truncate">{s.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{s.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { Card, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface EventsData {
  topButtons: { name: string; clicks: number; trend: string }[];
  trafficSources: { name: string; value: number; color: string }[];
  segmentGoal: { name: string; count: number }[];
  segmentLevel: { name: string; count: number }[];
}

export default function EventTracking() {
  const { data, isLoading } = useQuery<EventsData>({
    queryKey: ["admin_events"],
    queryFn: () => fetchApi("/api/admin/events"),
  });

  const topButtons = data?.topButtons || [];
  const trafficSources = data?.trafficSources || [];
  const segmentGoal = data?.segmentGoal || [];
  const segmentLevel = data?.segmentLevel || [];

  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Voqealar va bosishlar</h2>

      {/* Top Buttons */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-3">Ko'p bosilgan tugmalar</h3>
          {isLoading ? (
            <div className="text-xs text-muted-foreground text-center py-4">Yuklanmoqda...</div>
          ) : topButtons.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Hozircha ma'lumot yo'q</div>
          ) : (
            <div className="space-y-2">
              {topButtons.map((btn, i) => (
                <div key={btn.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-muted-foreground w-4">#{i + 1}</span>
                    <span className="text-xs font-medium">{btn.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">{btn.clicks.toLocaleString()}</span>
                    <span className={`text-[10px] font-medium ${btn.trend.startsWith("+") ? "text-success" : "text-destructive"}`}>
                      {btn.trend}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Traffic Sources */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Trafik manbalari</h3>
          {trafficSources.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Hozircha ma'lumot yo'q</div>
          ) : (
            <div className="flex items-center gap-4">
              <div className="w-28 h-28">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={trafficSources} cx="50%" cy="50%" innerRadius={28} outerRadius={48} dataKey="value" strokeWidth={0}>
                      {trafficSources.map((entry, idx) => (
                        <Cell key={idx} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 space-y-1.5">
                {trafficSources.map((s) => (
                  <div key={s.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                      <span className="text-[11px]">{s.name}</span>
                    </div>
                    <span className="text-[11px] font-semibold">{s.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Segmentation by Goal */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Maqsad bo'yicha</h3>
          {segmentGoal.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Hozircha ma'lumot yo'q</div>
          ) : (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={segmentGoal} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                  />
                  <Bar dataKey="count" fill="hsl(199, 85%, 55%)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Segmentation by Level */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <h3 className="text-sm font-semibold mb-2">Daraja bo'yicha</h3>
          {segmentLevel.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">Hozircha ma'lumot yo'q</div>
          ) : (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={segmentLevel} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                  />
                  <Bar dataKey="count" fill="hsl(142, 60%, 45%)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

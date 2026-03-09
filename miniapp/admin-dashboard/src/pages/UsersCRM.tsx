import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, X, UserCheck, UserX } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

type LeadScore = "hot" | "nurture" | "cold";
type UserStatusLabel = "paid" | "free" | "dropped";
type ActiveTab = "all" | "active" | "inactive";

interface CRMUser {
  id: number;
  name: string;
  phone: string;
  score: LeadScore;
  status: UserStatusLabel;
  isActive: boolean;
  source: string;
  registeredAt: string;
  events: { action: string; time: string }[];
}

const scoreColors: Record<LeadScore, string> = {
  hot: "bg-destructive/10 text-destructive",
  nurture: "bg-warning/10 text-warning",
  cold: "bg-muted text-muted-foreground",
};

const statusColors: Record<UserStatusLabel, string> = {
  paid: "bg-success/10 text-success",
  free: "bg-primary/10 text-primary",
  dropped: "bg-destructive/10 text-destructive",
};

const scoreLabel: Record<LeadScore, string> = {
  hot: "Issiq",
  nurture: "Iliq",
  cold: "Sovuq",
};
const statusLabel: Record<UserStatusLabel, string> = {
  paid: "To'lagan",
  free: "Bepul",
  dropped: "Ketgan",
};

const TABS: { id: ActiveTab; label: string; icon: React.ElementType }[] = [
  { id: "all", label: "Barchasi", icon: Search },
  { id: "active", label: "Aktiv", icon: UserCheck },
  { id: "inactive", label: "Nosaktiv", icon: UserX },
];

export default function UsersCRM() {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("all");
  const [filterScore, setFilterScore] = useState<LeadScore | "all">("all");
  const [selectedUser, setSelectedUser] = useState<CRMUser | null>(null);

  const { data: usersData, isLoading } = useQuery<CRMUser[]>({
    queryKey: ["admin_users", activeTab],
    queryFn: () => fetchApi(`/api/admin/users?status=${activeTab}`),
    refetchInterval: 30_000, // sinxron — har 30 soniyada yangilanadi
  });

  const users = usersData || [];

  const filtered = users.filter((u) => {
    const matchSearch =
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.id.toString().includes(search) ||
      u.phone.includes(search);
    const matchScore = filterScore === "all" || u.score === filterScore;
    return matchSearch && matchScore;
  });

  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Foydalanuvchilar (CRM)</h2>

      {/* Active / Inactive Tabs */}
      <div className="flex gap-1.5 p-1 bg-secondary rounded-xl">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-[11px] font-medium transition-all ${activeTab === tab.id
                ? "bg-card shadow text-foreground"
                : "text-muted-foreground"
              }`}
          >
            <tab.icon className="h-3 w-3" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Stats bar */}
      {!isLoading && (
        <div className="flex gap-2">
          <Card className="flex-1 glass-card border-border/30">
            <CardContent className="p-2 text-center">
              <p className="text-base font-bold text-foreground">{filtered.length}</p>
              <p className="text-[10px] text-muted-foreground">Natija</p>
            </CardContent>
          </Card>
          <Card className="flex-1 glass-card border-border/30">
            <CardContent className="p-2 text-center">
              <p className="text-base font-bold text-success">
                {filtered.filter(u => u.status === "paid").length}
              </p>
              <p className="text-[10px] text-muted-foreground">To'lagan</p>
            </CardContent>
          </Card>
          <Card className="flex-1 glass-card border-border/30">
            <CardContent className="p-2 text-center">
              <p className="text-base font-bold text-primary">
                {filtered.filter(u => u.score === "hot").length}
              </p>
              <p className="text-[10px] text-muted-foreground">Issiq lid</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <Input
          placeholder="Ism, ID yoki telefon..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8 h-9 text-xs bg-secondary border-border/30"
        />
      </div>

      {/* Score filters */}
      <div className="flex gap-1.5">
        {(["all", "hot", "nurture", "cold"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilterScore(s)}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${filterScore === s
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground"
              }`}
          >
            {s === "all" ? "Barchasi" : scoreLabel[s]}
          </button>
        ))}
      </div>

      {/* User List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="text-xs text-muted-foreground text-center p-6">Yuklanmoqda...</div>
        ) : filtered.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center p-6">
            {activeTab === "active" ? "Aktiv foydalanuvchilar topilmadi" :
              activeTab === "inactive" ? "Nosaktiv foydalanuvchilar topilmadi" :
                "Foydalanuvchilar topilmadi"}
          </div>
        ) : (
          filtered.map((user) => (
            <Card
              key={user.id}
              className="glass-card border-border/30 cursor-pointer hover:border-primary/30 transition-colors"
              onClick={() => setSelectedUser(user)}
            >
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${user.isActive ? "bg-green-500" : "bg-red-400"}`} />
                      <p className="text-sm font-semibold truncate">{user.name}</p>
                    </div>
                    <p className="text-[10px] text-muted-foreground ml-3">
                      #{user.id} · {user.source} · {user.registeredAt}
                    </p>
                  </div>
                  <div className="flex gap-1.5 ml-2">
                    <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${scoreColors[user.score]}`}>
                      {scoreLabel[user.score]}
                    </Badge>
                    <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${statusColors[user.status]}`}>
                      {statusLabel[user.status]}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* User Profile Modal */}
      <AnimatePresence>
        {selectedUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-end"
            onClick={() => setSelectedUser(null)}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="w-full max-h-[80vh] bg-card border-t border-border rounded-t-2xl p-4 overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${selectedUser.isActive ? "bg-green-500" : "bg-red-400"}`} />
                    <h3 className="text-base font-bold">{selectedUser.name}</h3>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {selectedUser.phone} · {selectedUser.source} · {selectedUser.registeredAt}
                  </p>
                </div>
                <button onClick={() => setSelectedUser(null)} className="p-1 rounded-full hover:bg-secondary">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 mb-4">
                <Badge className={scoreColors[selectedUser.score]}>{scoreLabel[selectedUser.score]}</Badge>
                <Badge className={statusColors[selectedUser.status]}>{statusLabel[selectedUser.status]}</Badge>
                <Badge className={selectedUser.isActive ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"}>
                  {selectedUser.isActive ? "Aktiv" : "Nosaktiv"}
                </Badge>
              </div>

              {selectedUser.events.length > 0 ? (
                <>
                  <h4 className="text-sm font-semibold mb-2">Bosib o'tgan yo'li</h4>
                  <div className="relative pl-4 border-l-2 border-primary/30 space-y-3">
                    {selectedUser.events.map((ev, i) => (
                      <div key={i} className="relative">
                        <div className="absolute -left-[calc(1rem+5px)] top-1 w-2 h-2 rounded-full bg-primary" />
                        <p className="text-xs font-medium">{ev.action}</p>
                        <p className="text-[10px] text-muted-foreground">{ev.time}</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-xs text-muted-foreground text-center py-4">Hozircha faollik yo'q</p>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Home, GitBranch, MousePointerClick, Users, Megaphone } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import DashboardHome from "@/pages/DashboardHome";
import FunnelAnalytics from "@/pages/FunnelAnalytics";
import EventTracking from "@/pages/EventTracking";
import UsersCRM from "@/pages/UsersCRM";
import Broadcast from "@/pages/Broadcast";
import CourseManager from "@/pages/CourseManager";

import GuidesManager from "@/pages/GuidesManager";
import LeadMagnetManager from "@/pages/LeadMagnetManager";

const tabs = [
  { id: "home", label: "Asosiy", icon: Home },
  { id: "funnel", label: "Voronka", icon: GitBranch },
  { id: "events", label: "Voqealar", icon: MousePointerClick },
  { id: "users", label: "Userlar", icon: Users },
  { id: "broadcast", label: "Xabarlar", icon: Megaphone },
  { id: "courses", label: "Darslar", icon: BookOpen },
  { id: "guides", label: "Qo'llanmalar", icon: BookOpen },
  { id: "magnets", label: "Promolar", icon: Gift },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function AppLayout() {
  const [activeTab, setActiveTab] = useState<TabId>("home");

  const renderScreen = () => {
    switch (activeTab) {
      case "home": return <DashboardHome />;
      case "funnel": return <FunnelAnalytics />;
      case "events": return <EventTracking />;
      case "users": return <UsersCRM />;
      case "broadcast": return <Broadcast />;
      case "courses": return <CourseManager />;
      case "guides": return <GuidesManager />;
      case "magnets": return <LeadMagnetManager />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <h1 className="text-lg font-bold text-gradient">Admin Boshqaruvi</h1>
        <ThemeToggle />
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="p-4 pb-24"
          >
            {renderScreen()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Bottom Tab Bar */}
      <nav className="fixed bottom-0 left-0 right-0 glass-card border-t border-border/30 px-2 pb-[env(safe-area-inset-bottom)]">
        <div className="flex items-center justify-around">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex flex-col items-center gap-0.5 py-2 px-3 transition-colors relative ${isActive ? "text-primary" : "text-muted-foreground"
                  }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute -top-px left-2 right-2 h-0.5 bg-primary rounded-full"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <tab.icon className="h-5 w-5" />
                <span className="text-[10px] font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

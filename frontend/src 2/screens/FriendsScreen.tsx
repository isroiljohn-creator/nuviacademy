import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, UserPlus, Trophy, Swords, ArrowLeft, Search, Crown, Medal, Award, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useToast } from '@/hooks/use-toast';

interface Friend {
  id: string;
  name: string;
  avatar?: string;
  level: number;
  xp: number;
  status: 'online' | 'offline';
}

interface LeaderboardEntry {
  rank: number;
  name: string;
  nameKey?: string;
  score: number;
  avatar?: string;
}

interface FriendsScreenProps {
  onBack?: () => void;
}

export const FriendsScreen: React.FC<FriendsScreenProps> = ({ onBack }) => {
  const { t } = useLanguage();
  const { toast } = useToast();
  const { profile, points } = useUser();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [friendRequests, setFriendRequests] = useState<any[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('friends');

  const fetchFriends = async () => {
    try {
      const token = localStorage.getItem('token');
      // Fetch Friends
      const res = await axios.get(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFriends(res.data);

      // Fetch Requests
      const reqRes = await axios.get(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/friends/requests`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFriendRequests(reqRes.data);

    } catch (e) {
      console.error("Fetch friends error:", e);
    }
  };

  const handleAcceptRequest = async (id: string, name: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/friends/requests/${id}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({
        title: "Qabul qilindi",
        description: `${name} bilan do'stlashdingiz!`,
      });
      fetchFriends();
    } catch (e) {
      console.error("Accept error:", e);
    }
  };

  const handleDeclineRequest = async (id: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/friends/requests/${id}/decline`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchFriends();
    } catch (e) {
      console.error("Decline error:", e);
    }
  };

  useEffect(() => {
    fetchFriends();
  }, []);

  // Search effect
  useEffect(() => {
    const searchTimer = setTimeout(async () => {
      if (searchQuery.length >= 3) {
        setIsSearching(true);
        try {
          const token = localStorage.getItem('token');
          const res = await axios.get(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/search?q=${searchQuery}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setSearchResults(res.data);
        } catch (e) {
          console.error("Search error:", e);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    }, 500);

    return () => clearTimeout(searchTimer);
  }, [searchQuery]);

  const leaderboard: LeaderboardEntry[] = [
    { rank: 1, nameKey: 'friends.you', name: profile?.name || '', score: points },
  ];

  const handleAddFriendFromSearch = async (userId: number, username: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_URL || '/api/v1'}/social/friends/request?to_user_id=${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({
        title: t('friends.requestSent'),
        description: `@${username} ${t('friends.requestSentDesc')}`,
      });
      setSearchQuery('');
      setSearchResults([]);
    } catch (e: any) {
      toast({
        title: t('common.error'),
        description: e.response?.data?.detail || "Xatolik yuz berdi",
        variant: "destructive",
      });
    }
  };

  const handleAddFriend = () => {
    if (!searchQuery.trim()) {
      toast({
        title: t('common.error'),
        description: t('friends.enterUsername'),
        variant: "destructive",
      });
      return;
    }
    // If there is only one result, add it
    if (searchResults.length === 1) {
      handleAddFriendFromSearch(searchResults[0].id, searchResults[0].username);
    } else if (searchResults.length > 1) {
      toast({
        title: "Ma'lumot",
        description: "Ro'yxatdan foydalanuvchini tanlang",
      });
    } else {
      toast({
        title: t('common.error'),
        description: "Foydalanuvchi topilmadi",
        variant: "destructive",
      });
    }
  };

  const handleChallenge = (friendName: string) => {
    toast({
      title: t('friends.challengeSent'),
      description: `${friendName} ${t('friends.challengeSentDesc')}`,
    });
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1: return <Crown className="w-5 h-5 text-yellow-400" />;
      case 2: return <Medal className="w-5 h-5 text-gray-400" />;
      case 3: return <Award className="w-5 h-5 text-amber-600" />;
      default: return <span className="text-muted-foreground font-bold">#{rank}</span>;
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen bg-background pb-28">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 safe-area-top">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2 rounded-full bg-card">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-foreground">{t('friends.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('friends.subtitle')}</p>
          </div>
        </div>

        {/* Search & Add Friend */}
        <div className="flex gap-2 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder={t('friends.search')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button onClick={handleAddFriend} size="icon">
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
          </Button>
        </div>

        {/* Search Results Dropdown */}
        <AnimatePresence>
          {searchResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-card border border-border rounded-2xl p-2 mb-6 shadow-xl"
            >
              {searchResults.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleAddFriendFromSearch(user.id, user.username)}
                  className="w-full flex items-center justify-between p-3 hover:bg-muted rounded-xl transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                      {user.username[0].toUpperCase()}
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-foreground">@{user.username}</p>
                      <p className="text-xs text-muted-foreground">{user.full_name}</p>
                    </div>
                  </div>
                  <UserPlus className="w-4 h-4 text-primary" />
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full">
            <TabsTrigger value="friends" className="flex-1">
              <Users className="w-4 h-4 mr-2" />
              {t('friends.friendsTab')}
            </TabsTrigger>
            <TabsTrigger value="leaderboard" className="flex-1">
              <Trophy className="w-4 h-4 mr-2" />
              {t('friends.leaderboard')}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="friends" className="mt-4">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-3"
            >
              {/* Requests */}
              {friendRequests.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-bold text-muted-foreground mb-2 flex items-center gap-2">
                    <UserPlus className="w-4 h-4" /> So'rovlar
                  </h3>
                  {friendRequests.map((req) => (
                    <motion.div
                      key={req.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-3 rounded-2xl bg-primary/5 border border-primary/20 mb-2 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary">
                          {req.fromUser.name[0]}
                        </div>
                        <div>
                          <p className="font-semibold text-foreground text-sm">{req.fromUser.name}</p>
                          <p className="text-xs text-muted-foreground">Level {req.fromUser.level}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="h-8 px-2 text-red-500 hover:text-red-600" onClick={() => handleDeclineRequest(req.id)}>
                          Rad etish
                        </Button>
                        <Button size="sm" className="h-8 px-3" onClick={() => handleAcceptRequest(req.id, req.fromUser.name)}>
                          Qabul
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {friends.length === 0 ? (
                <div className="text-center py-20 bg-card/30 rounded-3xl border border-dashed border-border">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-20" />
                  <p className="text-muted-foreground px-10">
                    {t('friends.noFriends') || "Hozircha do'stlar yo'q. Do'stingizni @username orqali qidirib toping."}
                  </p>
                </div>
              ) : friends.map((friend) => (
                <motion.div
                  key={friend.id}
                  variants={itemVariants}
                  className="p-4 rounded-2xl bg-card border border-border/50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center text-lg font-bold text-primary">
                          {friend.name[0]}
                        </div>
                        <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-card ${friend.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                          }`} />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">{friend.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Level {friend.level} • {friend.xp} XP
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleChallenge(friend.name)}
                      className="gap-1"
                    >
                      <Swords className="w-4 h-4" />
                      {t('friends.challenge')}
                    </Button>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </TabsContent>

          <TabsContent value="leaderboard" className="mt-4">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-2"
            >
              {leaderboard.map((entry, index) => {
                const displayName = entry.nameKey ? t(entry.nameKey) : entry.name;
                const isYou = entry.nameKey === 'friends.you';
                return (
                  <motion.div
                    key={entry.rank}
                    variants={itemVariants}
                    className={`p-4 rounded-2xl border ${entry.rank <= 3
                      ? 'bg-gradient-to-r from-primary/10 to-transparent border-primary/30'
                      : 'bg-card border-border/50'
                      } ${isYou ? 'ring-2 ring-primary' : ''}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-8 flex justify-center">
                          {getRankIcon(entry.rank)}
                        </div>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center font-bold text-primary">
                          {displayName[0]}
                        </div>
                        <div>
                          <p className={`font-semibold ${isYou ? 'text-primary' : 'text-foreground'}`}>
                            {displayName}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-foreground">{entry.score.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">XP</p>
                      </div>
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

import { useState, useRef, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Send, ImageIcon, Plus, ChevronDown, ChevronUp,
  X, FileText, Film, Mic, Video, RefreshCw, Link
} from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchApi, API_URL, getInitData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface AudienceCount {
  all: number;
  video_not_paid: number;
  hot: number;
  paid: number;
}

interface PastBroadcast {
  id: number;
  title: string;
  sent: number;
  total: number;
  failed: number;
  status: string;
  date: string;
}

interface BroadcastButton {
  text: string;
  url: string;
}

interface AttachedMedia {
  file: File;
  preview?: string;
  fileId?: string;
  contentType: string;
  uploading: boolean;
}

const AUDIENCE_LABELS = [
  { label: "Barchaga", key: "all" as keyof AudienceCount },
  { label: "Video ko'rgan (bepul)", key: "video_not_paid" as keyof AudienceCount },
  { label: "Issiq mijozlar", key: "hot" as keyof AudienceCount },
  { label: "To'laganlar", key: "paid" as keyof AudienceCount },
];

const MEDIA_ACCEPT = "image/*,video/*,audio/*,.pdf,.doc,.docx,.zip,.mp3";

function getMediaIcon(contentType: string) {
  if (contentType.startsWith("image")) return <ImageIcon className="h-4 w-4" />;
  if (contentType.startsWith("video")) return <Film className="h-4 w-4" />;
  if (contentType.startsWith("audio")) return <Mic className="h-4 w-4" />;
  if (contentType === "video_note") return <Video className="h-4 w-4" />;
  return <FileText className="h-4 w-4" />;
}

function mapMimeToTgType(mime: string): string {
  if (mime.startsWith("image/")) return "photo";
  if (mime.startsWith("video/")) return "video";
  if (mime.startsWith("audio/")) return "audio";
  return "document";
}

export default function Broadcast() {
  const [selectedAudience, setSelectedAudience] = useState(0);
  const [message, setMessage] = useState("");
  const [expandedBroadcast, setExpandedBroadcast] = useState<number | null>(null);
  const [media, setMedia] = useState<AttachedMedia | null>(null);
  const [buttons, setButtons] = useState<BroadcastButton[]>([]);
  const [showButtonForm, setShowButtonForm] = useState(false);
  const [btnText, setBtnText] = useState("");
  const [btnUrl, setBtnUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Fetch audience counts
  const { data: audienceCounts } = useQuery<AudienceCount>({
    queryKey: ["audience_counts"],
    queryFn: () => fetchApi("/api/admin/audience-counts"),
  });

  // Fetch & auto-refresh broadcast history (every 5s)
  const { data: broadcastHistory, refetch: refetchHistory } = useQuery<PastBroadcast[]>({
    queryKey: ["broadcast_history"],
    queryFn: () => fetchApi("/api/admin/broadcasts"),
    refetchInterval: 5000,
  });

  // Media upload mutation
  const uploadMedia = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const initData = getInitData();
      const response = await fetch(`${API_URL}/api/admin/upload-media-form`, {
        method: "POST",
        headers: initData ? { Authorization: `tma ${initData}` } : {},
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed: ${response.status}`);
      }
      return response.json() as Promise<{ file_id: string; content_type: string }>;
    },
    onSuccess: (data) => {
      setMedia((m) => m ? { ...m, fileId: data.file_id, contentType: data.content_type, uploading: false } : null);
      toast({ title: "✅ Media yuklandi", description: "Xabarni yuborishga tayyor." });
    },
    onError: (err: Error) => {
      setMedia(null);
      toast({ title: "Media xatolik", description: err.message, variant: "destructive" });
    },
  });

  const handleFileSelect = useCallback((file: File) => {
    const preview = file.type.startsWith("image") ? URL.createObjectURL(file) : undefined;
    const tgType = mapMimeToTgType(file.type);
    setMedia({ file, preview, contentType: tgType, uploading: true });
    uploadMedia.mutate(file);
  }, [uploadMedia]);

  const sendBroadcast = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {
        audience: selectedAudience,
        message: message.trim(),
      };
      if (media?.fileId) {
        payload.file_id = media.fileId;
        payload.content_type = media.contentType;
      }
      if (buttons.length > 0) {
        payload.buttons = buttons;
      }
      return fetchApi("/api/admin/broadcast", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (data) => {
      toast({
        title: "✅ Xabar yuborildi!",
        description: data.message || "Xabarlar tarqatilmoqda.",
      });
      setMessage("");
      setMedia(null);
      setButtons([]);
      refetchHistory();
      // Keep refreshing history
      setTimeout(() => refetchHistory(), 3000);
      setTimeout(() => refetchHistory(), 8000);
    },
    onError: (error: Error) => {
      toast({
        title: "Xatolik",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const addButton = () => {
    if (!btnText.trim() || !btnUrl.trim()) return;
    if (!btnUrl.startsWith("http://") && !btnUrl.startsWith("https://")) {
      toast({ title: "URL noto'g'ri", description: "URL https:// bilan boshlanishi kerak.", variant: "destructive" });
      return;
    }
    setButtons((prev) => [...prev, { text: btnText.trim(), url: btnUrl.trim() }]);
    setBtnText("");
    setBtnUrl("");
    setShowButtonForm(false);
  };

  const canSend = (message.trim().length > 0 || media?.fileId) && !sendBroadcast.isPending && !media?.uploading;

  const getCount = (key: keyof AudienceCount) => {
    const val = audienceCounts?.[key];
    return val != null ? val.toLocaleString() : "...";
  };

  return (
    <div className="space-y-4">
      <h2 className="text-base font-bold">Xabarlar yuborish</h2>

      {/* Composer */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3 space-y-3">
          <h3 className="text-sm font-semibold">Yangi xabar</h3>

          {/* Audience */}
          <div>
            <p className="text-[11px] text-muted-foreground mb-1.5">Auditoriya</p>
            <div className="flex flex-wrap gap-1.5">
              {AUDIENCE_LABELS.map((a, i) => (
                <button
                  key={a.key}
                  onClick={() => setSelectedAudience(i)}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${selectedAudience === i
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                    }`}
                >
                  {a.label} ({getCount(a.key)})
                </button>
              ))}
            </div>
          </div>

          {/* Attached Media Preview */}
          {media && (
            <div className="flex items-center gap-2 p-2 bg-secondary rounded-lg border border-border/30">
              {media.preview ? (
                <img src={media.preview} alt="preview" className="h-12 w-12 object-cover rounded" />
              ) : (
                <div className="h-12 w-12 flex items-center justify-center bg-muted rounded text-muted-foreground">
                  {getMediaIcon(media.file.type)}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{media.file.name}</p>
                <p className="text-[10px] text-muted-foreground">
                  {media.uploading ? "Yuklanmoqda..." : `✅ ${media.contentType}`}
                </p>
              </div>
              <button onClick={() => setMedia(null)} className="text-muted-foreground hover:text-destructive">
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Attached Buttons Preview */}
          {buttons.length > 0 && (
            <div className="space-y-1">
              <p className="text-[11px] text-muted-foreground">Qo'shilgan tugmalar:</p>
              {buttons.map((btn, i) => (
                <div key={i} className="flex items-center justify-between bg-secondary rounded px-2 py-1">
                  <div className="flex items-center gap-1.5">
                    <Link className="h-3 w-3 text-primary" />
                    <span className="text-xs font-medium">{btn.text}</span>
                    <span className="text-[10px] text-muted-foreground truncate max-w-[100px]">{btn.url}</span>
                  </div>
                  <button onClick={() => setButtons((b) => b.filter((_, idx) => idx !== i))}>
                    <X className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Button Form */}
          {showButtonForm && (
            <div className="space-y-2 p-2 bg-secondary/50 rounded-lg border border-border/30">
              <p className="text-[11px] font-medium">Tugma qo'shish</p>
              <Input
                placeholder="Tugma matni"
                value={btnText}
                onChange={(e) => setBtnText(e.target.value)}
                className="h-8 text-xs"
              />
              <Input
                placeholder="https://example.com"
                value={btnUrl}
                onChange={(e) => setBtnUrl(e.target.value)}
                className="h-8 text-xs"
              />
              <div className="flex gap-2">
                <Button size="sm" className="h-7 text-xs flex-1" onClick={addButton}>
                  Qo'shish
                </Button>
                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => setShowButtonForm(false)}>
                  Bekor
                </Button>
              </div>
            </div>
          )}

          {/* Message input */}
          <textarea
            placeholder="Xabaringizni yozing... (ixtiyoriy, agar media bo'lsa caption sifatida yuboriladi)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full h-20 text-xs bg-secondary border border-border/30 rounded-lg p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-primary"
          />

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept={MEDIA_ACCEPT}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelect(file);
              e.target.value = "";
            }}
          />

          {/* Actions */}
          <div className="flex items-center justify-between pt-1 border-t border-border/30">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs gap-1"
                onClick={() => fileInputRef.current?.click()}
                disabled={!!media}
              >
                <ImageIcon className="h-3.5 w-3.5" />
                Media
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs gap-1"
                onClick={() => setShowButtonForm((v) => !v)}
              >
                <Plus className="h-3.5 w-3.5" />
                Tugma
              </Button>
            </div>
            <Button
              size="sm"
              className="h-8 text-xs gap-1"
              disabled={!canSend}
              onClick={() => sendBroadcast.mutate()}
            >
              <Send className="h-3.5 w-3.5" />
              {sendBroadcast.isPending ? "Yuborilmoqda..." : media?.uploading ? "Yuklanmoqda..." : "Yuborish"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Past Broadcasts */}
      <Card className="glass-card border-border/30">
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Avvalgi xabarlar</h3>
            <button onClick={() => refetchHistory()} className="text-muted-foreground hover:text-foreground">
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="space-y-2">
            {!broadcastHistory ? (
              <div className="text-xs text-muted-foreground text-center py-2">Yuklanmoqda...</div>
            ) : broadcastHistory.length === 0 ? (
              <div className="text-xs text-muted-foreground text-center py-2">Hozircha xabar yuborilmagan</div>
            ) : (
              broadcastHistory.map((b) => {
                const isLive = b.status === "Yuborilmoqda";
                return (
                  <div key={b.id} className={`border rounded-lg p-2.5 ${isLive ? "border-primary/40 bg-primary/5" : "border-border/30"}`}>
                    <button
                      className="w-full flex items-center justify-between"
                      onClick={() => setExpandedBroadcast(expandedBroadcast === b.id ? null : b.id)}
                    >
                      <div className="text-left">
                        <p className="text-xs font-medium">{b.title}</p>
                        <p className="text-[10px] text-muted-foreground">{b.date}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="secondary"
                          className={`text-[10px] ${isLive ? "bg-primary/20 text-primary animate-pulse" : "bg-primary/10 text-primary"}`}
                        >
                          {b.status}
                        </Badge>
                        {expandedBroadcast === b.id ? (
                          <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                        )}
                      </div>
                    </button>
                    {expandedBroadcast === b.id && (
                      <div className="mt-2 pt-2 border-t border-border/30 grid grid-cols-3 gap-2">
                        <div className="text-center">
                          <p className="text-sm font-bold text-primary">{b.sent.toLocaleString()}</p>
                          <p className="text-[10px] text-muted-foreground">Yuborildi</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm font-bold text-success">{(b.sent - b.failed).toLocaleString()}</p>
                          <p className="text-[10px] text-muted-foreground">Yetkazildi</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm font-bold text-destructive">{b.failed.toLocaleString()}</p>
                          <p className="text-[10px] text-muted-foreground">Xato</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

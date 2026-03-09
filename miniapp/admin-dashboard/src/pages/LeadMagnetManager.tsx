import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Pencil, Link as LinkIcon, FileText, Video, File, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { fetchApi } from "@/lib/api";

interface LeadMagnet {
    id: number;
    campaign: string;
    content_type: string; // video, pdf, vsl
    file_id: string | null;
    file_url: string | null;
    description: string | null;
    is_active: boolean;
    created_at: string;
}

export default function LeadMagnetManager() {
    const queryClient = useQueryClient();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingMagnet, setEditingMagnet] = useState<LeadMagnet | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        campaign: "",
        content_type: "pdf",
        file_id: "",
        file_url: "",
        description: "",
        is_active: true,
    });

    const { data: magnets = [], isLoading } = useQuery<LeadMagnet[]>({
        queryKey: ["admin-lead-magnets"],
        queryFn: () => fetchApi("/admin/lead-magnets"),
    });

    const saveMutation = useMutation({
        mutationFn: (data: any) => {
            // Must not contain spaces or special chars for campaign/start link
            const cleanData = {
                ...data,
                campaign: data.campaign.trim().replace(/\s+/g, '_').toLowerCase()
            };

            if (editingMagnet) {
                return fetchApi(`/admin/lead-magnets/${editingMagnet.id}`, {
                    method: "PUT",
                    body: JSON.stringify(cleanData),
                });
            }
            return fetchApi("/admin/lead-magnets", {
                method: "POST",
                body: JSON.stringify(cleanData),
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-lead-magnets"] });
            toast.success(editingMagnet ? "Lid magnit yangilandi" : "Lid magnit qo'shildi");
            setIsDialogOpen(false);
            resetForm();
        },
        onError: (error) => toast.error(error.message),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/admin/lead-magnets/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-lead-magnets"] });
            toast.success("Lid magnit o'chirildi");
        },
        onError: (error) => toast.error(error.message),
    });

    const resetForm = () => {
        setEditingMagnet(null);
        setFormData({
            campaign: "",
            content_type: "pdf",
            file_id: "",
            file_url: "",
            description: "",
            is_active: true,
        });
    };

    const handleEdit = (lm: LeadMagnet) => {
        setEditingMagnet(lm);
        setFormData({
            campaign: lm.campaign,
            content_type: lm.content_type,
            file_id: lm.file_id || "",
            file_url: lm.file_url || "",
            description: lm.description || "",
            is_active: lm.is_active,
        });
        setIsDialogOpen(true);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.campaign) {
            toast.error("Kampaniya nomini kiriting");
            return;
        }
        saveMutation.mutate(formData);
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.success("Nusxa olindi: " + text);
    }

    const getFileIcon = (type: string) => {
        switch (type) {
            case "video": return <Video className="h-4 w-4" />;
            case "vsl": return <Video className="h-4 w-4" />;
            case "pdf": return <File className="h-4 w-4" />;
            default: return <FileText className="h-4 w-4" />;
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">🎁 Lid Magnitlar (Start Linklar)</h2>

                <Dialog open={isDialogOpen} onOpenChange={(open) => {
                    setIsDialogOpen(open);
                    if (!open) resetForm();
                }}>
                    <DialogTrigger asChild>
                        <Button size="sm" className="gap-2" onClick={resetForm}>
                            <Plus className="h-4 w-4" /> Qo'shish
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>{editingMagnet ? "Tahrirlash" : "Yangi lid magnit (Promokod)"}</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Kampaniya / Promokod (inglizcha, probelsiz)</label>
                                <Input
                                    value={formData.campaign}
                                    onChange={(e) => setFormData({ ...formData, campaign: e.target.value.replace(/\s+/g, '_').toLowerCase() })}
                                    placeholder="masalan: promt, video_darslik"
                                />
                                <p className="text-xs text-muted-foreground">Bot linki shunday bo'ladi: t.me/Isroil_AIBot?start=<b>{formData.campaign || 'kampaniya'}</b></p>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Qisqacha ta'rif / Matn</label>
                                <Textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Bot orqali yuboriladigan qisqacha ma'lumot..."
                                    rows={3}
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Format turi</label>
                                <Select
                                    value={formData.content_type}
                                    onValueChange={(val) => setFormData({ ...formData, content_type: val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="pdf">Hujjat (PDF/Doc/Photo)</SelectItem>
                                        <SelectItem value="video">Video Darslik</SelectItem>
                                        <SelectItem value="vsl">VSL (Maxsus Video)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2 p-3 bg-secondary/20 rounded-lg border border-border">
                                <label className="text-sm font-medium flex items-center gap-2">
                                    <LinkIcon className="h-4 w-4" /> Telegram File ID
                                </label>
                                <Input
                                    value={formData.file_id}
                                    onChange={(e) => setFormData({ ...formData, file_id: e.target.value, file_url: "" })}
                                    placeholder="BQACAgIAAxkBA..."
                                />
                            </div>

                            <div className="flex items-center gap-2 pt-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="w-full"
                                    onClick={() => setFormData({ ...formData, is_active: !formData.is_active })}
                                >
                                    Holati: {formData.is_active ? "🟢 Aktiv" : "🔴 Aktiv emas"}
                                </Button>
                            </div>

                            <div className="pt-4 flex gap-2">
                                <Button type="button" variant="outline" className="flex-1" onClick={() => setIsDialogOpen(false)}>
                                    Bekor qilish
                                </Button>
                                <Button type="submit" className="flex-1" disabled={saveMutation.isPending}>
                                    {saveMutation.isPending ? "Saqlanmoqda..." : "Saqlash"}
                                </Button>
                            </div>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm flex gap-3 text-blue-200">
                <LinkIcon className="h-5 w-5 shrink-0 text-blue-400" />
                <p>
                    Ushbu sahifada siz maxsus <b>/start</b> linklarini yaratishingiz mumkin. Bu link (masalan, <code>?start=promt</code>) orqali kiritilgan foydalanuvchilarga avtomat tarzda kerakli resurs beriladi va ro'yxatdan o'tkaziladi.
                </p>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : magnets.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-muted-foreground">
                    <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Hozircha lid magnitlar yo'q.</p>
                </div>
            ) : (
                <div className="grid gap-3">
                    {magnets.map((magnet) => (
                        <div key={magnet.id} className="glass-card p-4 rounded-xl flex items-center justify-between gap-4">
                            <div className="flex gap-4 items-start flex-1 min-w-0">
                                <div className={"p-2 rounded-lg shrink-0 " + (magnet.is_active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground")}>
                                    {getFileIcon(magnet.content_type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className={"font-semibold truncate " + (!magnet.is_active && "text-muted-foreground line-through")}>
                                            {magnet.campaign}
                                        </h3>
                                        <span className="text-xs uppercase font-bold text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                                            {magnet.content_type}
                                        </span>
                                    </div>

                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="bg-background border px-2 py-1 rounded text-xs font-mono text-muted-foreground flex-1 truncate">
                                            t.me/Isroil_AIBot?start={magnet.campaign}
                                        </div>
                                        <Button size="icon" variant="outline" className="h-7 w-7 shrink-0" onClick={() => copyToClipboard(`https://t.me/Isroil_AIBot?start=${magnet.campaign}`)}>
                                            <Copy className="h-3 w-3" />
                                        </Button>
                                    </div>

                                    {magnet.description && (
                                        <p className="text-sm text-muted-foreground truncate">
                                            {magnet.description}
                                        </p>
                                    )}
                                    {magnet.file_id && (
                                        <p className="text-xs text-blue-500 font-mono truncate mt-1 inline-flex items-center gap-1">
                                            <LinkIcon className="h-3 w-3" /> Fayl biriktirilgan
                                        </p>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                                <Button size="icon" variant="secondary" onClick={() => handleEdit(magnet)}>
                                    <Pencil className="h-4 w-4" />
                                </Button>
                                <Button size="icon" variant="destructive" onClick={() => {
                                    if (confirm("Rostdan ham o'chirmoqchimisiz?")) {
                                        deleteMutation.mutate(magnet.id);
                                    }
                                }}>
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

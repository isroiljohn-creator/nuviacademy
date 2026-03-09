import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Pencil, Link as LinkIcon, FileText, Video, File, BookOpen } from "lucide-react";
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

interface Guide {
    id: number;
    title: string;
    content: string | null;
    file_id: string | null;
    file_type: string | null;
    media_url: string | null;
    is_active: boolean;
    order: number;
    created_at: string;
}

export default function GuidesManager() {
    const queryClient = useQueryClient();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingGuide, setEditingGuide] = useState<Guide | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        title: "",
        content: "",
        file_type: "text",
        file_id: "",
        media_url: "",
        is_active: true,
        order: 0,
    });

    const { data: guides = [], isLoading } = useQuery<Guide[]>({
        queryKey: ["admin-guides"],
        queryFn: () => fetchApi("/admin/guides"),
    });

    const saveMutation = useMutation({
        mutationFn: (data: any) => {
            if (editingGuide) {
                return fetchApi(`/admin/guides/${editingGuide.id}`, {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            }
            return fetchApi("/admin/guides", {
                method: "POST",
                body: JSON.stringify(data),
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-guides"] });
            toast.success(editingGuide ? "Qo'llanma yangilandi" : "Qo'llanma qo'shildi");
            setIsDialogOpen(false);
            resetForm();
        },
        onError: (error) => toast.error(error.message),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/admin/guides/${id}`, { method: "DELETE" }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-guides"] });
            toast.success("Qo'llanma o'chirildi");
        },
        onError: (error) => toast.error(error.message),
    });

    const resetForm = () => {
        setEditingGuide(null);
        setFormData({
            title: "",
            content: "",
            file_type: "text",
            file_id: "",
            media_url: "",
            is_active: true,
            order: 0,
        });
    };

    const handleEdit = (guide: Guide) => {
        setEditingGuide(guide);
        setFormData({
            title: guide.title,
            content: guide.content || "",
            file_type: guide.file_type || "text",
            file_id: guide.file_id || "",
            media_url: guide.media_url || "",
            is_active: guide.is_active,
            order: guide.order,
        });
        setIsDialogOpen(true);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title) {
            toast.error("Sarlavhani kiriting");
            return;
        }
        saveMutation.mutate(formData);
    };

    const getFileIcon = (type: string | null) => {
        switch (type) {
            case "video": return <Video className="h-4 w-4" />;
            case "document": return <File className="h-4 w-4" />;
            case "photo": return <FileText className="h-4 w-4" />;
            default: return <FileText className="h-4 w-4" />;
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">📚 Qo'llanmalar</h2>

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
                            <DialogTitle>{editingGuide ? "Tahrirlash" : "Yangi qo'llanma"}</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Sarlavha</label>
                                <Input
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="Macbook o'rnatish qo'llanmasi"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Matn ma'lumoti</label>
                                <Textarea
                                    value={formData.content}
                                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                    placeholder="To'liq ta'rif yoki qadam-ba-qadam qo'llanma..."
                                    rows={4}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Format turi</label>
                                    <Select
                                        value={formData.file_type}
                                        onValueChange={(val) => setFormData({ ...formData, file_type: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="text">Faqat Matn</SelectItem>
                                            <SelectItem value="video">Video</SelectItem>
                                            <SelectItem value="document">Hujjat (PDF/Doc)</SelectItem>
                                            <SelectItem value="photo">Rasm</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Tartib</label>
                                    <Input
                                        type="number"
                                        value={formData.order}
                                        onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 0 })}
                                    />
                                </div>
                            </div>

                            {formData.file_type !== "text" && (
                                <div className="space-y-2 p-3 bg-secondary/20 rounded-lg border border-border">
                                    <label className="text-sm font-medium flex items-center gap-2">
                                        <LinkIcon className="h-4 w-4" /> Telegram File ID yoki Havola
                                    </label>
                                    <Input
                                        value={formData.file_id}
                                        onChange={(e) => setFormData({ ...formData, file_id: e.target.value, media_url: "" })}
                                        placeholder="BQACAgIAAxkBA..."
                                        className="mb-2"
                                    />
                                    <div className="text-center text-xs text-muted-foreground my-1">YOKI E'LON HAVOLASI</div>
                                    <Input
                                        value={formData.media_url}
                                        onChange={(e) => setFormData({ ...formData, media_url: e.target.value, file_id: "" })}
                                        placeholder="https://youtube.com/..."
                                    />
                                </div>
                            )}

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

            {isLoading ? (
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : guides.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-muted-foreground">
                    <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Hozircha qo'llanmalar yo'q.</p>
                </div>
            ) : (
                <div className="grid gap-3">
                    {guides.map((guide) => (
                        <div key={guide.id} className="glass-card p-4 rounded-xl flex items-center justify-between gap-4">
                            <div className="flex gap-4 items-start flex-1 min-w-0">
                                <div className={"p-2 rounded-lg shrink-0 " + (guide.is_active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground")}>
                                    {getFileIcon(guide.file_type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className={"font-semibold truncate " + (!guide.is_active && "text-muted-foreground line-through")}>
                                            {guide.title}
                                        </h3>
                                        <span className="text-xs font-mono text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                                            #{guide.id} (Tartib: {guide.order})
                                        </span>
                                    </div>
                                    {guide.content && (
                                        <p className="text-sm text-muted-foreground truncate mt-1">
                                            {guide.content}
                                        </p>
                                    )}
                                    {guide.file_id && (
                                        <p className="text-xs text-blue-500 font-mono truncate mt-1 inline-flex items-center gap-1">
                                            <LinkIcon className="h-3 w-3" /> file_id biriktirilgan
                                        </p>
                                    )}
                                    {guide.media_url && (
                                        <p className="text-xs text-purple-500 truncate mt-1 inline-flex items-center gap-1">
                                            <LinkIcon className="h-3 w-3" /> {guide.media_url}
                                        </p>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                                <Button size="icon" variant="secondary" onClick={() => handleEdit(guide)}>
                                    <Pencil className="h-4 w-4" />
                                </Button>
                                <Button size="icon" variant="destructive" onClick={() => {
                                    if (confirm("Rostdan ham o'chirmoqchimisiz?")) {
                                        deleteMutation.mutate(guide.id);
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

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/use-toast";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Trash2, Edit2, Plus, GripVertical, PlayCircle } from "lucide-react";

interface CourseModule {
    id: number;
    title: string;
    description: string | null;
    video_url: string | null;
    video_file_id: string | null;
    order: number;
    is_active: boolean;
    unlock_condition: string | null;
}

export default function CourseManager() {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingModule, setEditingModule] = useState<CourseModule | null>(null);

    // Form State
    const [formData, setFormData] = useState({
        title: "",
        description: "",
        video_url: "",
        video_file_id: "",
        order: 1,
        is_active: true,
    });

    const { data: courses, isLoading } = useQuery<CourseModule[]>({
        queryKey: ["adminCourses"],
        queryFn: () => fetchApi("/api/admin/courses"),
    });

    const createMutation = useMutation({
        mutationFn: (newModule: any) => fetchApi("/api/admin/courses", {
            method: "POST",
            body: JSON.stringify(newModule),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "Muvaffaqiyatli", description: "Dars qo'shildi" });
            setIsModalOpen(false);
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    const updateMutation = useMutation({
        mutationFn: (updated: any) => fetchApi(`/api/admin/courses/${updated.id}`, {
            method: "PUT",
            body: JSON.stringify(updated.data),
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "Muvaffaqiyatli", description: "Dars yangilandi" });
            setIsModalOpen(false);
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => fetchApi(`/api/admin/courses/${id}`, {
            method: "DELETE",
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
            toast({ title: "Muvaffaqiyatli", description: "Dars o'chirildi" });
        },
        onError: (error: any) => {
            toast({ title: "Xatolik", description: error.message, variant: "destructive" });
        },
    });

    const handleOpenModal = (mod: CourseModule | null = null) => {
        if (mod) {
            setEditingModule(mod);
            setFormData({
                title: mod.title || "",
                description: mod.description || "",
                video_url: mod.video_url || "",
                video_file_id: mod.video_file_id || "",
                order: mod.order || 1,
                is_active: mod.is_active ?? true,
            });
        } else {
            setEditingModule(null);
            const nextOrder = courses ? courses.length + 1 : 1;
            setFormData({
                title: "",
                description: "",
                video_url: "",
                video_file_id: "",
                order: nextOrder,
                is_active: true,
            });
        }
        setIsModalOpen(true);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const payload = {
            title: formData.title,
            description: formData.description || null,
            video_url: formData.video_url || null,
            video_file_id: formData.video_file_id || null,
            order: Number(formData.order),
            is_active: formData.is_active,
        };

        if (editingModule) {
            updateMutation.mutate({ id: editingModule.id, data: payload });
        } else {
            createMutation.mutate(payload);
        }
    };

    const handleDelete = (id: number) => {
        if (confirm("Rostdan ham ushbu darsni o'chirmoqchimisiz?")) {
            deleteMutation.mutate(id);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight">📚 Bepul Darslar</h2>
                <Button onClick={() => handleOpenModal()} className="gap-2">
                    <Plus className="w-4 h-4" /> Yangi Dars
                </Button>
            </div>

            <div className="grid gap-4">
                {isLoading ? (
                    <div className="flex justify-center p-8"><span className="animate-spin text-2xl">⏳</span></div>
                ) : courses && courses.length > 0 ? (
                    courses.map((course) => (
                        <Card key={course.id} className={`transition-all duration-200 ${!course.is_active ? 'opacity-60' : ''}`}>
                            <CardContent className="p-4 flex items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                                        {course.order}
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{course.title}</h3>
                                        <p className="text-sm text-muted-foreground line-clamp-1">
                                            {course.description || "Ta'rif yo'q"}
                                        </p>
                                        <div className="flex gap-2 mt-1 text-xs items-center text-muted-foreground">
                                            {course.video_file_id ? (
                                                <span className="flex items-center gap-1 text-blue-500"><PlayCircle className="w-3 h-3" /> Telegram ID</span>
                                            ) : course.video_url ? (
                                                <span className="flex items-center gap-1 text-purple-500"><PlayCircle className="w-3 h-3" /> Tashqi Havola</span>
                                            ) : (
                                                <span className="text-destructive">⚠️ Video yo'q</span>
                                            )}
                                            {!course.is_active && <span className="text-destructive font-semibold px-2">Yashirilgan</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="icon" onClick={() => handleOpenModal(course)}>
                                        <Edit2 className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(course.id)}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <div className="text-center p-8 text-muted-foreground border border-dashed rounded-lg">
                        Hali darslar qo'shilmagan.
                    </div>
                )}
            </div>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{editingModule ? "Darsni Tahrirlash" : "Yangi Dars Qo'shish"}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Sarlavha (Title)</Label>
                            <Input required value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} placeholder="Misol: 1-dars. Kirish" />
                        </div>
                        <div className="space-y-2">
                            <Label>Telegram Video ID <span className="text-xs text-muted-foreground">(Tavsiya etiladi)</span></Label>
                            <Input value={formData.video_file_id} onChange={e => setFormData({ ...formData, video_file_id: e.target.value })} placeholder="BAQADAgADxyz..." />
                        </div>
                        <div className="space-y-2">
                            <Label>Yoki Tashqi Video URL (Link)</Label>
                            <Input value={formData.video_url} onChange={e => setFormData({ ...formData, video_url: e.target.value })} placeholder="https://youtube.com/..." />
                        </div>
                        <div className="space-y-2">
                            <Label>Ta'rif (Description)</Label>
                            <Textarea value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} placeholder="Dars haqida qisqacha ma'lumot..." />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Tartib raqami</Label>
                                <Input type="number" required value={formData.order} onChange={e => setFormData({ ...formData, order: Number(e.target.value) })} />
                            </div>
                            <div className="flex flex-col justify-center space-y-2 pt-6">
                                <div className="flex items-center gap-2">
                                    <Switch checked={formData.is_active} onCheckedChange={c => setFormData({ ...formData, is_active: c })} />
                                    <Label>Aktivmi?</Label>
                                </div>
                            </div>
                        </div>
                        <DialogFooter className="pt-4">
                            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Bekor qilish</Button>
                            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                                {editingModule ? "Saqlash" : "Qo'shish"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
}

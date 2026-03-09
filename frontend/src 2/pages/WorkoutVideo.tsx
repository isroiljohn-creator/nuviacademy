import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export default function WorkoutVideo() {
    const [searchParams] = useSearchParams();
    const exerciseName = searchParams.get("exercise") || searchParams.get("day") || "";

    const [videoUrl, setVideoUrl] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchVideo = async () => {
            try {
                // Use generic search term if day parameter provided
                const searchTerm = searchParams.get("exercise") || "mashq";

                const response = await axios.get(`${API_BASE}/api/v1/content/video_url`, {
                    params: { exercise_name: searchTerm }
                });
                setVideoUrl(response.data.video_url);
            } catch (err: any) {
                setError(err.response?.data?.detail || "Video topilmadi");
            } finally {
                setLoading(false);
            }
        };

        fetchVideo();
    }, [exerciseName, searchParams]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
                    <p>Yuklanmoqda...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
                <div className="text-center p-6">
                    <p className="text-xl mb-4">❌</p>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-4xl">
                <h1 className="text-2xl font-bold text-white mb-4 text-center">{exerciseName}</h1>
                <div className="bg-black rounded-lg overflow-hidden shadow-2xl">
                    <video
                        controls
                        autoPlay
                        playsInline
                        className="w-full"
                        src={videoUrl}
                    >
                        Brauzeringiz video formatini qo'llab-quvvatlamaydi.
                    </video>
                </div>
                <p className="text-gray-400 text-center mt-4 text-sm">
                    💡 Video Telegram kanalidan yuklanmoqda
                </p>
            </div>
        </div>
    );
}

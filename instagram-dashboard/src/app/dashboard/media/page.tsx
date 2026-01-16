"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Download, CheckCircle2, Image as ImageIcon, Film } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

// Mock Media Data
const MOCK_MEDIA = Array.from({ length: 12 }).map((_, i) => ({
    id: `media-${i}`,
    type: i % 3 === 0 ? "video" : "image",
    url: `/api/placeholder?id=${i}`, // Placeholder
    date: "2024-03-10",
    likes: 120 + i * 10,
}));

export default function MediaPage() {
    const [selected, setSelected] = useState<string[]>([]);
    const [isDownloading, setIsDownloading] = useState(false);

    const toggleSelection = (id: string) => {
        setSelected((prev) =>
            prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
        );
    };

    const handleDownload = () => {
        setIsDownloading(true);
        // Simulate generic download process
        setTimeout(() => {
            setIsDownloading(false);
            alert(`Downloaded ${selected.length > 0 ? selected.length : "ALL"} items!`);
            setSelected([]);
        }, 2000);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Media Gallery</h2>
                    <p className="text-muted-foreground">
                        Select photos and videos to backup or download your entire archive.
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={() => setSelected([])}
                        disabled={selected.length === 0}
                    >
                        Clear Selection
                    </Button>
                    <Button onClick={handleDownload} disabled={isDownloading}>
                        {isDownloading ? (
                            "Processing..."
                        ) : (
                            <>
                                <Download className="mr-2 h-4 w-4" />
                                {selected.length > 0 ? `Download (${selected.length})` : "Backup All Data"}
                            </>
                        )}
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {MOCK_MEDIA.map((item, index) => {
                    const isSelected = selected.includes(item.id);

                    return (
                        <motion.div
                            key={item.id}
                            layout
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <Card
                                className={cn(
                                    "group relative cursor-pointer overflow-hidden border-0 bg-secondary/50 transition-all hover:bg-secondary aspect-square",
                                    isSelected && "ring-2 ring-primary"
                                )}
                                onClick={() => toggleSelection(item.id)}
                            >
                                <div className="absolute inset-0 bg-zinc-800 flex items-center justify-center text-zinc-700">
                                    {/* Placeholder Visual if no image */}
                                    {item.type === 'video' ? <Film className="w-12 h-12 opacity-20" /> : <ImageIcon className="w-12 h-12 opacity-20" />}
                                </div>

                                {/* Overlay */}
                                <div className={cn(
                                    "absolute inset-0 bg-black/40 transition-opacity flex items-center justify-center opacity-0 group-hover:opacity-100",
                                    isSelected && "opacity-100 bg-primary/20"
                                )}>
                                    {isSelected ? (
                                        <CheckCircle2 className="w-8 h-8 text-white drop-shadow-lg" />
                                    ) : (
                                        <div className="text-white text-sm font-medium">Click to select</div>
                                    )}
                                </div>

                                <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <span className="text-xs text-white/80 bg-black/50 px-2 py-1 rounded-full">{item.date}</span>
                                </div>
                            </Card>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}

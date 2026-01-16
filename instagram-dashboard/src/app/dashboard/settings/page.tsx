"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    User,
    Bell,
    Shield,
    Download,
    Trash2,
    Moon,
    Check
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SettingSection {
    id: string;
    title: string;
    description: string;
    icon: typeof User;
}

const settingSections: SettingSection[] = [
    { id: "profile", title: "Profile", description: "Manage your account settings", icon: User },
    { id: "notifications", title: "Notifications", description: "Configure alert preferences", icon: Bell },
    { id: "privacy", title: "Privacy & Security", description: "Control your data and access", icon: Shield },
    { id: "appearance", title: "Appearance", description: "Customize the dashboard look", icon: Moon },
];

export default function SettingsPage() {
    const [activeSection, setActiveSection] = useState("profile");
    const [saving, setSaving] = useState(false);

    const handleSave = () => {
        setSaving(true);
        setTimeout(() => {
            setSaving(false);
        }, 1500);
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">
                    Manage your account preferences and dashboard configuration.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-4">
                {/* Settings Navigation */}
                <Card className="bg-card/40 backdrop-blur-md border-white/5 md:col-span-1">
                    <CardContent className="p-4">
                        <nav className="space-y-1">
                            {settingSections.map((section) => {
                                const Icon = section.icon;
                                const isActive = activeSection === section.id;
                                return (
                                    <button
                                        key={section.id}
                                        onClick={() => setActiveSection(section.id)}
                                        className={cn(
                                            "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all",
                                            isActive
                                                ? "bg-primary/10 text-primary border border-primary/20"
                                                : "text-muted-foreground hover:bg-white/5 hover:text-white"
                                        )}
                                    >
                                        <Icon className="w-4 h-4" />
                                        <span className="text-sm font-medium">{section.title}</span>
                                    </button>
                                );
                            })}
                        </nav>
                    </CardContent>
                </Card>

                {/* Settings Content */}
                <div className="md:col-span-3 space-y-4">
                    {activeSection === "profile" && (
                        <Card className="bg-card/40 backdrop-blur-md border-white/5">
                            <CardHeader>
                                <CardTitle>Profile Settings</CardTitle>
                                <CardDescription>Update your account information</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                                        <User className="w-8 h-8 text-white" />
                                    </div>
                                    <div>
                                        <p className="font-medium">@your_username</p>
                                        <p className="text-sm text-muted-foreground">Connected via Instagram API</p>
                                    </div>
                                </div>

                                <div className="space-y-3 pt-4 border-t border-white/10">
                                    <div>
                                        <label className="text-sm font-medium">Display Name</label>
                                        <input
                                            type="text"
                                            defaultValue="Your Name"
                                            className="mt-1 w-full bg-secondary/50 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Email</label>
                                        <input
                                            type="email"
                                            defaultValue="you@example.com"
                                            className="mt-1 w-full bg-secondary/50 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {activeSection === "notifications" && (
                        <Card className="bg-card/40 backdrop-blur-md border-white/5">
                            <CardHeader>
                                <CardTitle>Notification Preferences</CardTitle>
                                <CardDescription>Choose what updates you receive</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {["Weekly analytics report", "New follower milestones", "Engagement alerts", "System updates"].map((item, i) => (
                                    <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                        <span className="text-sm">{item}</span>
                                        <div className="w-10 h-6 bg-primary/20 rounded-full relative cursor-pointer">
                                            <div className="absolute right-0.5 top-0.5 w-5 h-5 bg-primary rounded-full" />
                                        </div>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    )}

                    {activeSection === "privacy" && (
                        <Card className="bg-card/40 backdrop-blur-md border-white/5">
                            <CardHeader>
                                <CardTitle>Privacy & Security</CardTitle>
                                <CardDescription>Manage your data and security settings</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center gap-3">
                                    <Check className="w-5 h-5 text-emerald-500" />
                                    <div>
                                        <p className="font-medium text-emerald-400">Account Connected</p>
                                        <p className="text-sm text-muted-foreground">Your Instagram account is securely linked</p>
                                    </div>
                                </div>

                                <div className="space-y-3 pt-4">
                                    <Button variant="outline" className="w-full justify-start gap-2">
                                        <Download className="w-4 h-4" />
                                        Export All Data
                                    </Button>
                                    <Button variant="outline" className="w-full justify-start gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10">
                                        <Trash2 className="w-4 h-4" />
                                        Delete Account
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {activeSection === "appearance" && (
                        <Card className="bg-card/40 backdrop-blur-md border-white/5">
                            <CardHeader>
                                <CardTitle>Appearance</CardTitle>
                                <CardDescription>Customize how the dashboard looks</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="text-sm font-medium mb-2 block">Theme</label>
                                    <div className="flex gap-3">
                                        <div className="w-20 h-14 bg-zinc-900 border-2 border-primary rounded-lg flex items-center justify-center cursor-pointer">
                                            <span className="text-xs">Dark</span>
                                        </div>
                                        <div className="w-20 h-14 bg-zinc-100 border border-white/20 rounded-lg flex items-center justify-center cursor-pointer opacity-50">
                                            <span className="text-xs text-zinc-900">Light</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-white/10">
                                    <label className="text-sm font-medium mb-2 block">Accent Color</label>
                                    <div className="flex gap-2">
                                        {["#c026d3", "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b"].map((color) => (
                                            <div
                                                key={color}
                                                className={cn(
                                                    "w-8 h-8 rounded-full cursor-pointer transition-transform hover:scale-110",
                                                    color === "#c026d3" && "ring-2 ring-white ring-offset-2 ring-offset-zinc-900"
                                                )}
                                                style={{ backgroundColor: color }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <Button onClick={handleSave} disabled={saving} className="min-w-[120px]">
                            {saving ? "Saving..." : "Save Changes"}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}

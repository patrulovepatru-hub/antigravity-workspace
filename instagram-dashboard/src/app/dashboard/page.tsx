"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Heart, TrendingUp, ArrowUpRight, LucideIcon } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock Data
const data = [
    { name: 'Mon', followers: 4000 },
    { name: 'Tue', followers: 4200 },
    { name: 'Wed', followers: 4800 },
    { name: 'Thu', followers: 5100 },
    { name: 'Fri', followers: 5400 },
    { name: 'Sat', followers: 5900 },
    { name: 'Sun', followers: 6200 },
];

interface StatCardProps {
    title: string;
    value: string;
    change: string;
    icon: LucideIcon;
}

const StatCard = ({ title, value, change, icon: Icon }: StatCardProps) => (
    <Card className="bg-card/40 backdrop-blur-md border-white/5 hover:bg-card/60 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
            <Icon className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
            <div className="text-2xl font-bold">{value}</div>
            <p className="text-xs text-muted-foreground flex items-center mt-1">
                <span className="text-emerald-500 flex items-center mr-1">
                    <ArrowUpRight className="h-3 w-3 mr-1" />
                    {change}
                </span>
                from last week
            </p>
        </CardContent>
    </Card>
);

export default function DashboardPage() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
                <p className="text-muted-foreground">Welcome back. Here&apos;s what&apos;s happening with your account.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatCard title="Total Followers" value="12,345" change="+12.5%" icon={Users} />
                <StatCard title="Avg. Engagement" value="4.8%" change="+2.1%" icon={Heart} />
                <StatCard title="Reach" value="45.2k" change="+18.2%" icon={TrendingUp} />
                <StatCard title="Impressions" value="89.1k" change="+5.4%" icon={TrendingUp} />
            </div>

            {/* Main Chart Section */}
            <div className="grid gap-4 md:grid-cols-7">
                <Card className="col-span-4 bg-card/40 backdrop-blur-md border-white/5">
                    <CardHeader>
                        <CardTitle>Follower Growth</CardTitle>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data}>
                                    <defs>
                                        <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#c026d3" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#c026d3" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="name" stroke="#888" tickLine={false} axisLine={false} />
                                    <YAxis stroke="#888" tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area type="monotone" dataKey="followers" stroke="#c026d3" strokeWidth={2} fillOpacity={1} fill="url(#colorFollowers)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Posts / Activity Mock */}
                <Card className="col-span-3 bg-card/40 backdrop-blur-md border-white/5">
                    <CardHeader>
                        <CardTitle>Recent Posts</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group">
                                    <div className="w-12 h-12 bg-zinc-800 rounded-md overflow-hidden relative">
                                        {/* Placeholder for image */}
                                        <div className="absolute inset-0 bg-gradient-to-br from-zinc-700 to-zinc-900" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium leading-none mb-1 group-hover:text-primary transition-colors">Sunset in Bali</p>
                                        <div className="flex items-center text-xs text-muted-foreground gap-3">
                                            <span className="flex items-center gap-1"><Heart className="w-3 h-3" /> 1.2k</span>
                                            <span className="flex items-center gap-1">💬 45</span>
                                        </div>
                                    </div>
                                    <div className="text-xs text-muted-foreground whitespace-nowrap">
                                        2h ago
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { ArrowUp, ArrowDown } from "lucide-react";

const engagementData = [
    { name: 'Reels', value: 8500 },
    { name: 'Carousels', value: 6200 },
    { name: 'Static', value: 3400 },
    { name: 'Stories', value: 4100 },
];

const demographicsData = [
    { name: '18-24', value: 30 },
    { name: '25-34', value: 45 },
    { name: '35-44', value: 15 },
    { name: '45+', value: 10 },
];

const COLORS = ['#c026d3', '#db2777', '#9333ea', '#4f46e5'];

export default function AnalyticsPage() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Analytics Deep Dive</h2>
                <p className="text-muted-foreground">Detailed breakdown of your content performance and audience.</p>
            </div>

            {/* Top Metrics Row */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border-primary/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-purple-200">Avg. Reel Views</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">12.4k</div>
                        <p className="text-xs text-purple-300 flex items-center mt-1">
                            <ArrowUp className="w-3 h-3 mr-1" /> +24% vs last month
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Profile Visits</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">1,892</div>
                        <p className="text-xs text-muted-foreground flex items-center mt-1">
                            <ArrowDown className="w-3 h-3 mr-1 text-red-500" /> -4% vs last month
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Website Clicks</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">432</div>
                        <p className="text-xs text-muted-foreground flex items-center mt-1">
                            <ArrowUp className="w-3 h-3 mr-1 text-emerald-500" /> +12% vs last month
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 h-[500px]">
                {/* Engagement by Type Chart */}
                <Card className="col-span-4 bg-card/40 border-white/5">
                    <CardHeader>
                        <CardTitle>Engagement by Content Type</CardTitle>
                        <CardDescription>Reels are currently driving the most interaction.</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={engagementData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="name" stroke="#888" tickLine={false} axisLine={false} />
                                <YAxis stroke="#888" tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
                                    cursor={{ fill: '#ffffff10' }}
                                />
                                <Bar dataKey="value" fill="#c026d3" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Demographics Pie Chart */}
                <Card className="col-span-3 bg-card/40 border-white/5">
                    <CardHeader>
                        <CardTitle>Audience Age</CardTitle>
                        <CardDescription>Majority of followers are 25-34.</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={demographicsData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {demographicsData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0)" />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                                <Legend verticalAlign="bottom" height={36} />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

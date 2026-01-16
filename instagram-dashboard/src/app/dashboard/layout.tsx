import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-background text-foreground overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto relative h-screen">
                {/* Ambient background effects for the dashboard area */}
                <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-[-1]">
                    <div className="absolute top-[5%] right-[5%] w-[400px] h-[400px] bg-primary/5 rounded-full blur-[100px]" />
                    <div className="absolute bottom-[5%] left-[20%] w-[300px] h-[300px] bg-blue-500/5 rounded-full blur-[100px]" />
                </div>
                <div className="p-8 max-w-7xl mx-auto space-y-8">
                    {children}
                </div>
            </main>
        </div>
    );
}

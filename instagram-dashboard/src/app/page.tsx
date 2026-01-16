import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Instagram } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-background relative overflow-hidden">
      {/* Background Gradient Effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[120px]" />

      <Card className="w-full max-w-md bg-card/50 backdrop-blur-xl border-white/10 relative z-10 shadow-2xl">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto bg-gradient-to-br from-purple-500 to-pink-500 w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg mb-4">
            <Instagram className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            InstaAnalytics
          </CardTitle>
          <CardDescription className="text-lg">
            Master your social presence.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-muted-foreground text-sm px-6">
            Access deep insights, follower tracking, and secure media backups with our verified platform.
          </p>
          <div className="pt-4">
            <Button className="w-full h-12 text-md font-semibold bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition-opacity">
              Connect Instagram
            </Button>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground/60">
              Secure connection via Official Instagram Graph API
            </p>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

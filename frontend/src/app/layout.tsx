import type { Metadata } from "next";
import { AppSidebar } from "@/components/layout/app-sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentDevInsight",
  description: "Agent 评估与可观测性平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="flex min-h-screen">
          <AppSidebar />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}

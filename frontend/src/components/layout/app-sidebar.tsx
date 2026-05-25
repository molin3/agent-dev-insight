"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListTree,
  Database,
  FlaskConical,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/traces", label: "Traces", icon: ListTree },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/evaluations", label: "Evaluations", icon: BarChart3 },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-border h-screen bg-white flex-shrink-0">
      <div className="p-4 border-b border-border">
        <h1 className="text-lg font-bold text-primary">AgentDevInsight</h1>
        <p className="text-xs text-muted-foreground">Agent Observability</p>
      </div>
      <nav className="p-2 space-y-1">
        {navItems.map((item) => {
          const active = item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              )}
            >
              <item.icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

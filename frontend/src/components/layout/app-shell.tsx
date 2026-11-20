"use client";

import {
  Activity,
  FlaskConical,
  History,
  Menu,
  Sparkles,
  TerminalSquare,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { ConnectionSelector } from "@/components/layout/connection-selector";
import { DeterministicGuardHud } from "@/components/layout/deterministic-guard-hud";
import { useConnection } from "@/components/providers/connection-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Workbench", icon: TerminalSquare },
  { href: "/analytics", label: "Analytics", icon: Activity },
  { href: "/evals", label: "EvalOps", icon: FlaskConical },
  { href: "/sandbox", label: "Sandbox", icon: Sparkles },
  { href: "/history", label: "History", icon: History },
] as const;

export function AppShell({ children }: { readonly children: ReactNode }) {
  const pathname = usePathname();
  const { health, healthLoading } = useConnection();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const dbConnected = health?.database_status === "connected";

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-4">
        <Link href="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-90">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-accent-primary/40 bg-accent-primary/15 text-accent-primary shadow-xs shadow-accent-primary/20">
            <TerminalSquare className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-text-primary">
              AI SQL Detective
            </p>
            <p className="font-mono text-[11px] text-text-secondary">PostgreSQL 16</p>
          </div>
        </Link>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Close navigation menu"
          className="md:hidden"
          onClick={() => setMobileNavOpen(false)}
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>

      <nav aria-label="Primary" className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              onClick={() => setMobileNavOpen(false)}
              className={cn(
                "flex min-h-9 items-center gap-2.5 rounded-md px-3 py-2 text-xs font-medium transition-all duration-150",
                active
                  ? "border border-border-subtle bg-card text-text-primary shadow-xs"
                  : "border border-transparent text-text-secondary hover:bg-card-hover hover:text-text-primary",
              )}
            >
              <Icon
                className={cn("h-4 w-4", active ? "text-accent-primary" : "text-text-secondary")}
                aria-hidden="true"
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border-subtle p-3">
        <DeterministicGuardHud health={health} />
      </div>
    </div>
  );

  return (
    <div className="flex min-h-dvh bg-canvas text-text-primary">
      <a
        href="#main-content"
        className="skip-link fixed left-3 top-3 z-50 rounded-md border border-accent-primary bg-card px-3 py-2 text-xs font-medium text-text-primary shadow-sm"
      >
        Skip to main content
      </a>

      {/* Desktop Sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-border-subtle bg-surface md:block">
        {sidebarContent}
      </aside>

      {/* Mobile Navigation Drawer */}
      {mobileNavOpen ? (
        <div className="fixed inset-0 z-40 flex md:hidden" role="dialog" aria-label="Navigation">
          <div
            className="fixed inset-0 bg-canvas/80 backdrop-blur-xs"
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative z-10 w-64 border-r border-border-subtle bg-surface">
            {sidebarContent}
          </aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex min-h-14 flex-wrap items-center justify-between gap-3 border-b border-border-subtle bg-surface/90 px-4 py-2 backdrop-blur-sm lg:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Open navigation menu"
              className="md:hidden"
              onClick={() => setMobileNavOpen(true)}
            >
              <Menu className="h-4 w-4" aria-hidden="true" />
            </Button>
            <ConnectionSelector />
          </div>

          <div className="flex items-center gap-2 font-mono text-xs tabular-nums">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                healthLoading
                  ? "bg-status-warning"
                  : dbConnected
                    ? "bg-status-success shadow-xs shadow-status-success/50"
                    : "bg-status-error shadow-xs shadow-status-error/50",
              )}
              aria-hidden="true"
            />
            <span className="text-text-secondary">
              {healthLoading
                ? "Connecting..."
                : health
                  ? `API ${health.status.toUpperCase()} · DB ${health.database_status}`
                  : "Backend unreachable"}
            </span>
          </div>
        </header>

        <main id="main-content" tabIndex={-1} className="min-w-0 flex-1 outline-none">
          {children}
        </main>
      </div>
    </div>
  );
}

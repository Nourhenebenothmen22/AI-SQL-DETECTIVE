import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ConnectionProvider } from "@/components/providers/connection-provider";
import { QueryProvider } from "@/components/providers/query-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Workbench | AI SQL Detective",
  description:
    "AI-powered PostgreSQL workbench with deterministic read-only security validation, SSE agent progress, and query optimization.",
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#0B1020",
};

interface RootLayoutProps {
  readonly children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-dvh bg-canvas text-text-primary antialiased font-sans">
        <QueryProvider>
          <ConnectionProvider>
            <AppShell>{children}</AppShell>
          </ConnectionProvider>
        </QueryProvider>
      </body>
    </html>
  );
}

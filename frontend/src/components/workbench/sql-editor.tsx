"use client";

import type { OnMount } from "@monaco-editor/react";
import { Check, Code2, Copy, Play, ShieldCheck, ShieldX } from "lucide-react";
import dynamic from "next/dynamic";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => <Skeleton className="h-56 w-full rounded-none" />,
});

interface SqlEditorProps {
  sql: string;
  onSqlChange: (value: string) => void;
  onValidate: () => void;
  onExecute: () => void;
  isValidating: boolean;
  isExecuting: boolean;
  securityStatus: "passed" | "blocked" | null;
  enforcedLimit: number | null;
}

export function SqlEditor({
  sql,
  onSqlChange,
  onValidate,
  onExecute,
  isValidating,
  isExecuting,
  securityStatus,
  enforcedLimit,
}: SqlEditorProps) {
  const [copied, setCopied] = useState(false);

  const handleMount: OnMount = (editor, monaco) => {
    monaco.editor.defineTheme("ai-sql-detective-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "6366F1", fontStyle: "bold" },
        { token: "string", foreground: "10B981" },
        { token: "number", foreground: "06B6D4" },
        { token: "comment", foreground: "64748B", fontStyle: "italic" },
        { token: "operator", foreground: "94A3B8" },
        { token: "delimiter", foreground: "94A3B8" },
      ],
      colors: {
        "editor.background": "#070A12",
        "editor.foreground": "#F8FAFC",
        "editor.lineHighlightBackground": "#0D121F",
        "editorLineNumber.foreground": "#64748B",
        "editorLineNumber.activeForeground": "#94A3B8",
        "editor.selectionBackground": "#6366F135",
        "editorCursor.foreground": "#06B6D4",
        "editorGutter.background": "#070A12",
      },
    });
    monaco.editor.setTheme("ai-sql-detective-dark");

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onExecute();
    });
  };

  const handleCopy = async () => {
    if (!sql.trim()) return;
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="overflow-hidden rounded-lg border border-border-subtle bg-card shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-subtle bg-surface px-3.5 py-2">
        <div className="flex items-center gap-2.5">
          <Code2 className="h-4 w-4 text-accent-secondary" aria-hidden="true" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-primary">
            SQL Editor
          </h2>
          {securityStatus === "passed" ? (
            <Badge variant="success">
              <ShieldCheck className="h-3 w-3" aria-hidden="true" />
              Validated{enforcedLimit ? ` · LIMIT ${enforcedLimit}` : ""}
            </Badge>
          ) : securityStatus === "blocked" ? (
            <Badge variant="error">
              <ShieldX className="h-3 w-3" aria-hidden="true" />
              Blocked by Security Gate
            </Badge>
          ) : (
            <Badge variant="default">PostgreSQL 16 · Read-Only</Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void handleCopy()}
            disabled={!sql.trim()}
            aria-label="Copy SQL query"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-status-success" aria-hidden="true" />
            ) : (
              <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            <span>{copied ? "Copied" : "Copy"}</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onValidate}
            disabled={isValidating || isExecuting || !sql.trim()}
          >
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{isValidating ? "Validating..." : "Validate"}</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={onExecute}
            disabled={isExecuting || !sql.trim()}
          >
            <Play className="h-3.5 w-3.5 fill-current" aria-hidden="true" />
            <span>{isExecuting ? "Running..." : "Run Read-Only"}</span>
            <kbd className="ml-0.5 hidden rounded bg-black/30 px-1 py-0.5 font-mono text-[10px] text-white/70 sm:inline-block">
              Ctrl+↵
            </kbd>
          </Button>
        </div>
      </div>

      <div className="h-56 w-full bg-canvas">
        <MonacoEditor
          height="100%"
          defaultLanguage="pgsql"
          value={sql}
          onChange={(val) => onSqlChange(val ?? "")}
          onMount={handleMount}
          options={{
            minimap: { enabled: false },
            fontFamily: "var(--font-jetbrains-mono), monospace",
            fontSize: 13,
            lineHeight: 20,
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: "line",
            tabSize: 2,
          }}
        />
      </div>
    </section>
  );
}

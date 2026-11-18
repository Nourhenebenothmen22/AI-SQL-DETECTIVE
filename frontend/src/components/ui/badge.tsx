import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded border px-2 py-0.5 font-mono text-[11px] font-medium leading-tight",
  {
    variants: {
      variant: {
        default: "border-border-subtle bg-surface text-text-secondary",
        indigo: "border-accent-primary/40 bg-accent-primary/15 text-text-primary",
        cyan: "border-accent-secondary/40 bg-accent-secondary/10 text-accent-secondary",
        success: "border-status-success/40 bg-status-success/15 text-status-success",
        warning: "border-status-warning/40 bg-status-warning/15 text-status-warning",
        error: "border-status-error/40 bg-status-error/15 text-status-error",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

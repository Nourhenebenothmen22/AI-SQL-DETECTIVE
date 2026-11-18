import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex min-h-8 items-center justify-center gap-2 rounded-md text-xs font-medium transition-colors duration-150 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-accent-primary text-text-primary hover:bg-accent-primary/90 border border-accent-primary/40",
        secondary:
          "bg-card text-text-primary hover:bg-card/80 border border-border-subtle",
        outline:
          "bg-transparent text-text-primary hover:bg-card border border-border-subtle",
        ghost: "bg-transparent text-text-secondary hover:bg-card hover:text-text-primary",
        danger:
          "bg-status-error/15 text-status-error hover:bg-status-error/25 border border-status-error/40",
      },
      size: {
        sm: "h-8 px-2.5 text-xs",
        md: "h-9 px-3.5 text-sm",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "secondary",
      size: "sm",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  type = "button",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      type={asChild ? undefined : type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

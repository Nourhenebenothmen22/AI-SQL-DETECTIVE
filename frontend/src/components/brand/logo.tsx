import { cn } from "@/lib/utils";

interface LogoIconProps {
  className?: string;
  size?: number;
}

export function LogoIcon({ className, size = 32 }: LogoIconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      fill="none"
      width={size}
      height={size}
      className={cn("shrink-0 select-none", className)}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="logo-bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0F172A" />
          <stop offset="50%" stopColor="#090E17" />
          <stop offset="100%" stopColor="#030712" />
        </linearGradient>

        <linearGradient id="logo-border-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
          <stop offset="50%" stopColor="#6366F1" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#34D399" stopOpacity="0.6" />
        </linearGradient>

        <linearGradient id="logo-cyan-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>

        <linearGradient id="logo-emerald-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#34D399" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>

        <linearGradient id="logo-violet-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="100%" stopColor="#6366F1" />
        </linearGradient>

        <radialGradient id="logo-ai-core-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
          <stop offset="60%" stopColor="#0284C7" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#0284C7" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Hexagonal Shield Container */}
      <rect
        x="3"
        y="3"
        width="58"
        height="58"
        rx="16"
        fill="url(#logo-bg-grad)"
        stroke="url(#logo-border-glow)"
        strokeWidth="1.5"
      />

      {/* Database Disks (PostgreSQL Layered Architecture) */}
      <path
        d="M15 36c0 3 6.7 5.5 15 5.5s15-2.5 15-5.5v4c0 3-6.7 5.5-15 5.5s-15-2.5-15-5.5v-4z"
        fill="#1E293B"
        fillOpacity="0.7"
        stroke="#334155"
        strokeWidth="1.2"
      />
      <circle cx="17.5" cy="38" r="1.5" fill="url(#logo-emerald-glow)" />

      <path
        d="M15 28c0 3 6.7 5.5 15 5.5s15-2.5 15-5.5v4c0 3-6.7 5.5-15 5.5s-15-2.5-15-5.5v-4z"
        fill="#0F172A"
        fillOpacity="0.8"
        stroke="#38BDF8"
        strokeWidth="1.2"
        strokeOpacity="0.5"
      />
      <circle cx="17.5" cy="30" r="1.5" fill="url(#logo-cyan-glow)" />

      <ellipse
        cx="30"
        cy="20"
        rx="15"
        ry="5.5"
        fill="#1E293B"
        fillOpacity="0.8"
        stroke="#38BDF8"
        strokeWidth="1.2"
        strokeOpacity="0.6"
      />
      <circle cx="17.5" cy="22" r="1.5" fill="url(#logo-violet-glow)" />

      {/* AI Detective Magnifier Core */}
      <circle cx="37" cy="31" r="14" fill="url(#logo-ai-core-glow)" />
      <circle
        cx="37"
        cy="31"
        r="12"
        fill="#070A12"
        fillOpacity="0.8"
        stroke="url(#logo-cyan-glow)"
        strokeWidth="2.5"
      />
      <path
        d="M29 25a12 12 0 0 1 14 -3"
        stroke="#F8FAFC"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeOpacity="0.9"
      />

      {/* Cognitive Aperture & Spark */}
      <circle cx="37" cy="31" r="4.5" fill="#0F172A" stroke="url(#logo-emerald-glow)" strokeWidth="1.5" />
      <path d="M37 28v6M34 31h6" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="37" cy="31" r="1.2" fill="#FFFFFF" />

      {/* Magnifier Handle / Cyber Probe */}
      <path d="M45.5 39.5L53 47" stroke="url(#logo-cyan-glow)" strokeWidth="3" strokeLinecap="round" />
      <path d="M48 42l4 4" stroke="#FFFFFF" strokeWidth="1.2" strokeLinecap="round" strokeOpacity="0.8" />
      <circle cx="53" cy="47" r="2" fill="url(#logo-emerald-glow)" />
    </svg>
  );
}

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  showSubtitle?: boolean;
}

export function Logo({ className, size = "md", showSubtitle = true }: LogoProps) {
  const iconSizes = {
    sm: 28,
    md: 34,
    lg: 42,
  };

  return (
    <div className={cn("flex items-center gap-2.5 transition-transform hover:scale-[1.01]", className)}>
      <div className="relative flex items-center justify-center">
        <LogoIcon size={iconSizes[size]} />
      </div>

      <div className="flex flex-col leading-tight">
        <div className="flex items-center gap-1.5">
          <span className="font-sans font-bold tracking-tight text-text-primary text-[14px]">
            AI SQL
          </span>
          <span className="rounded-sm border border-sky-500/40 bg-sky-500/15 px-1.5 py-0.5 font-mono text-[9.5px] font-bold tracking-wider text-sky-300 shadow-xs shadow-sky-500/20 uppercase">
            Detective
          </span>
        </div>
        {showSubtitle ? (
          <span className="font-mono text-[10.5px] text-text-secondary tracking-tight">
            PostgreSQL 16 · Autonomous FinOps
          </span>
        ) : null}
      </div>
    </div>
  );
}

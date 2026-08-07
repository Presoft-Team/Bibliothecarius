import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-accent-600 text-white hover:bg-accent-700 focus-visible:outline-accent-600 disabled:hover:bg-accent-600",
  secondary:
    "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus-visible:outline-accent-600 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-800",
  danger:
    "bg-white text-red-600 border border-red-200 hover:bg-red-50 focus-visible:outline-red-600 dark:bg-slate-900 dark:border-red-900/50 dark:hover:bg-red-950/40",
  ghost:
    "bg-transparent text-slate-600 hover:bg-slate-100 focus-visible:outline-accent-600 dark:text-slate-300 dark:hover:bg-slate-800",
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: "px-2.5 py-1.5 text-xs",
  md: "px-3.5 py-2 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

export default function Button({
  variant = "secondary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

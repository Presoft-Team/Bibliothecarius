import type { ReactNode } from "react";

type Variant = "default" | "accent" | "warn" | "danger";

const VARIANT_CLASSES: Record<Variant, string> = {
  default: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  accent: "bg-accent-100 text-accent-700 dark:bg-accent-900/50 dark:text-accent-300",
  warn: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  danger: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
};

export default function Badge({
  variant = "default",
  children,
}: {
  variant?: Variant;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}

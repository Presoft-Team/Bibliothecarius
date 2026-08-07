import type { ReactNode } from "react";

export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30 disabled:bg-slate-50 disabled:text-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:disabled:bg-slate-800/50";

export default function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={`mb-3 block ${className}`}>
      <span className="mb-1 block text-xs font-semibold text-slate-600 dark:text-slate-400">
        {label}
      </span>
      {children}
    </label>
  );
}

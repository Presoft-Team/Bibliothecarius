import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export default function Card({ className = "", children, ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

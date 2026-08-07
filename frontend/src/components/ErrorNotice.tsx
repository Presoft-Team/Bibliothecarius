import { AlertTriangle } from "lucide-react";
import { summarizeProviderError } from "../lib/errors";

export default function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
      <div className="flex items-center gap-2 font-medium">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        {summarizeProviderError(message)}
      </div>
      <details className="mt-1 pl-6">
        <summary className="cursor-pointer text-xs text-red-600/80 hover:text-red-700 dark:text-red-400/80 dark:hover:text-red-300">
          Show details
        </summary>
        <pre className="mt-1 whitespace-pre-wrap text-xs text-red-600/90 dark:text-red-400/90">{message}</pre>
      </details>
    </div>
  );
}

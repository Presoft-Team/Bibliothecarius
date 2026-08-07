import { useEffect, useRef, useState } from "react";
import { Download, Trash2 } from "lucide-react";
import { llmApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import Card from "./ui/Card";
import Button from "./ui/Button";
import { inputClass } from "./ui/Field";

export default function OllamaModelsPanel() {
  const [models, setModels] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [newModelName, setNewModelName] = useState("");
  const [pulling, setPulling] = useState<string | null>(null);
  const [pullProgress, setPullProgress] = useState<{ completed: number; total: number } | null>(null);
  const [pullError, setPullError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadModels = () =>
    llmApi
      .listModels("ollama")
      .then((list) => {
        setModels(list);
        setLoadError(null);
      })
      .catch((err) => setLoadError(getErrorMessage(err, "Could not reach Ollama")));

  useEffect(() => {
    loadModels();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPull = async () => {
    const name = newModelName.trim();
    if (!name) return;
    setPullError(null);
    setPulling(name);
    setPullProgress({ completed: 0, total: 0 });
    await llmApi.pullOllamaModel(name);

    pollRef.current = setInterval(async () => {
      const status = await llmApi.ollamaPullStatus(name);
      if (status.status === "pulling") {
        setPullProgress({ completed: status.completed, total: status.total });
        return;
      }
      if (pollRef.current) clearInterval(pollRef.current);
      setPulling(null);
      setPullProgress(null);
      if (status.status === "error") {
        setPullError(status.error ?? "Pull failed");
      } else {
        setNewModelName("");
        loadModels();
      }
    }, 1500);
  };

  const removeModel = async (name: string) => {
    if (!confirm(`Delete "${name}" from Ollama? This frees disk space but anyone using it as a default will hit an error until they pick another model.`)) {
      return;
    }
    await llmApi.removeOllamaModel(name);
    loadModels();
  };

  const progressPct =
    pullProgress && pullProgress.total > 0 ? Math.round((pullProgress.completed / pullProgress.total) * 100) : null;

  return (
    <Card>
      <h2 className="mb-1 text-sm font-semibold text-slate-500 dark:text-slate-400">Local Ollama models</h2>
      <p className="mb-3 text-xs text-slate-400">
        Pull any model from Ollama's library (e.g. <code>llama3.2</code>, <code>qwen2.5:7b</code>,{" "}
        <code>mistral</code>) — larger models need more RAM/VRAM and take longer to download.
      </p>

      {loadError && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      <div className="mb-3 space-y-1.5">
        {models.map((m) => (
          <div key={m} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-1.5 text-sm dark:border-slate-700">
            <code className="text-slate-700 dark:text-slate-200">{m}</code>
            <button
              className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
              onClick={() => removeModel(m)}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
        {models.length === 0 && !loadError && <p className="text-sm text-slate-400">No models pulled yet.</p>}
      </div>

      <div className="flex gap-1.5">
        <input
          name="ollama-model-name"
          className={inputClass}
          placeholder="Model name, e.g. llama3.2"
          value={newModelName}
          onChange={(e) => setNewModelName(e.target.value)}
          disabled={!!pulling}
          onKeyDown={(e) => e.key === "Enter" && startPull()}
        />
        <Button disabled={!newModelName.trim() || !!pulling} onClick={startPull}>
          <Download className="h-4 w-4" />
          Pull
        </Button>
      </div>

      {pulling && (
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Pulling {pulling}
          {progressPct !== null ? ` — ${progressPct}%` : "…"}
        </p>
      )}
      {pullError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{pullError}</p>}
    </Card>
  );
}

import { useEffect, useState } from "react";
import { KeyRound, Trash2 } from "lucide-react";
import { assistantConfigApi, providerCredentialsApi, tonesApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import { useAuth } from "../lib/AuthContext";
import ModelPicker from "../components/ModelPicker";
import OllamaModelsPanel from "../components/OllamaModelsPanel";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import type { AssistantConfig, CloudProvider, ProviderCredential, Tone } from "../lib/types";

const CLOUD_PROVIDERS: CloudProvider[] = ["anthropic", "openai", "gemini"];

export default function AssistantSettingsPage() {
  const { currentUser } = useAuth();
  const [config, setConfig] = useState<AssistantConfig | null>(null);
  const [tones, setTones] = useState<Tone[]>([]);
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newKeyProvider, setNewKeyProvider] = useState<CloudProvider | "">("");
  const [newKeyValue, setNewKeyValue] = useState("");
  const [editValues, setEditValues] = useState<Record<string, string>>({});

  const loadCredentials = () => providerCredentialsApi.list().then(setCredentials);

  useEffect(() => {
    Promise.all([assistantConfigApi.get(), tonesApi.list(), providerCredentialsApi.list()]).then(
      ([cfg, toneList, creds]) => {
        setConfig(cfg);
        setTones(toneList);
        setCredentials(creds);
      }
    );
  }, []);

  if (!config) return <p className="text-sm text-slate-400">Loading…</p>;

  const update = (patch: Partial<AssistantConfig>) => setConfig({ ...config, ...patch });

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await assistantConfigApi.update({
        name: config.name,
        persona_description: config.persona_description,
        default_tone_id: config.default_tone_id,
        default_provider: config.default_provider,
        default_model: config.default_model,
        temperature: config.temperature,
        max_context_chunks: config.max_context_chunks,
      });
      setConfig(updated);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to save assistant settings"));
    } finally {
      setSaving(false);
    }
  };

  const addKey = async () => {
    if (!newKeyProvider || !newKeyValue) return;
    await providerCredentialsApi.set(newKeyProvider, newKeyValue);
    setNewKeyProvider("");
    setNewKeyValue("");
    loadCredentials();
  };

  const updateKey = async (provider: string) => {
    const value = editValues[provider];
    if (!value) return;
    await providerCredentialsApi.set(provider, value);
    setEditValues((prev) => ({ ...prev, [provider]: "" }));
    loadCredentials();
  };

  const removeKey = async (provider: string) => {
    await providerCredentialsApi.remove(provider);
    loadCredentials();
  };

  const configuredProviders = new Set(credentials.map((c) => c.provider));
  const unconfiguredProviders = CLOUD_PROVIDERS.filter((p) => !configuredProviders.has(p));

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Assistant Settings</h1>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400">Persona</h2>

        <Field label="Assistant name">
          <input
            name="assistant-name"
            className={inputClass}
            value={config.name}
            onChange={(e) => update({ name: e.target.value })}
          />
        </Field>

        <Field label="Persona description">
          <textarea
            name="persona-description"
            className={inputClass}
            rows={3}
            value={config.persona_description}
            onChange={(e) => update({ persona_description: e.target.value })}
          />
        </Field>

        <Field label="Default tone">
          <select
            name="default-tone"
            className={inputClass}
            value={config.default_tone_id ?? ""}
            onChange={(e) => update({ default_tone_id: e.target.value || null })}
          >
            <option value="">None</option>
            {tones.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </Field>

        <h2 className="mb-3 mt-5 text-sm font-semibold text-slate-500 dark:text-slate-400">Model</h2>

        <Field label="Default provider">
          <select
            name="default-provider"
            className={inputClass}
            value={config.default_provider}
            onChange={(e) =>
              update({
                default_provider: e.target.value as AssistantConfig["default_provider"],
                default_model: "",
              })
            }
          >
            <option value="ollama">Ollama (local)</option>
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Gemini</option>
          </select>
        </Field>

        <Field label="Default model">
          <ModelPicker
            provider={config.default_provider}
            value={config.default_model}
            onChange={(model) => update({ default_model: model })}
          />
        </Field>

        <Field label={`Temperature (${config.temperature.toFixed(1)})`}>
          <input
            name="temperature"
            type="range"
            min={0}
            max={1.5}
            step={0.1}
            className="w-full accent-accent-600"
            value={config.temperature}
            onChange={(e) => update({ temperature: Number(e.target.value) })}
          />
        </Field>

        <Field label="Max context chunks">
          <input
            name="max-context-chunks"
            className={inputClass}
            type="number"
            min={1}
            max={20}
            value={config.max_context_chunks}
            onChange={(e) => update({ max_context_chunks: Number(e.target.value) })}
          />
        </Field>

        {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <Button variant="primary" disabled={saving} onClick={save}>
          Save settings
        </Button>
      </Card>

      <Card>
        <h2 className="mb-1 text-sm font-semibold text-slate-500 dark:text-slate-400">
          Cloud provider API keys
        </h2>
        <p className="mb-3 text-xs text-slate-400">
          Stored encrypted at rest. Only needed for providers other than the local Ollama option.
        </p>

        <div className="space-y-3">
          {credentials.map((c) => (
            <div key={c.provider} className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
              <div className="flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2 text-sm">
                  <KeyRound className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                  <strong className="shrink-0 text-slate-700 dark:text-slate-200">{c.provider}</strong>
                  <code className="min-w-0 truncate text-xs text-slate-500 dark:text-slate-400">
                    {c.key_hint === "????" ? "(update below to reveal the last 4 digits)" : `•••• ${c.key_hint}`}
                  </code>
                </div>
                <button
                  className="shrink-0 rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                  onClick={() => removeKey(c.provider)}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-2 flex gap-1.5">
                <input
                  name={`replace-key-${c.provider}`}
                  autoComplete="off"
                  className={inputClass}
                  type="password"
                  placeholder="Replace key…"
                  value={editValues[c.provider] ?? ""}
                  onChange={(e) => setEditValues((prev) => ({ ...prev, [c.provider]: e.target.value }))}
                />
                <Button size="sm" disabled={!editValues[c.provider]} onClick={() => updateKey(c.provider)}>
                  Update
                </Button>
              </div>
            </div>
          ))}
          {credentials.length === 0 && <p className="text-sm text-slate-400">No API keys on file yet.</p>}
        </div>

        {unconfiguredProviders.length > 0 && (
          <div className="mt-3 flex gap-1.5">
            <select
              name="new-key-provider"
              className={inputClass}
              value={newKeyProvider}
              onChange={(e) => setNewKeyProvider(e.target.value as CloudProvider)}
            >
              <option value="">Add a key for…</option>
              {unconfiguredProviders.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <input
              name="new-key-value"
              autoComplete="off"
              className={inputClass}
              type="password"
              placeholder="API key"
              value={newKeyValue}
              onChange={(e) => setNewKeyValue(e.target.value)}
            />
            <Button onClick={addKey} disabled={!newKeyProvider || !newKeyValue}>
              Save key
            </Button>
          </div>
        )}
      </Card>

      {currentUser?.role === "admin" && <OllamaModelsPanel />}
    </div>
  );
}

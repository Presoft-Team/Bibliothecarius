import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { tonesApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Field, { inputClass } from "../components/ui/Field";
import type { Tone } from "../lib/types";

const EMPTY_FORM = { name: "", description: "", system_prompt_template: "", is_default: false };

export default function TonesPage() {
  const [tones, setTones] = useState<Tone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    tonesApi
      .list()
      .then(setTones)
      .catch(() => setError("Failed to load tones"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const selectTone = (tone: Tone | null) => {
    setSelectedId(tone?.id ?? null);
    setForm(
      tone
        ? {
            name: tone.name,
            description: tone.description,
            system_prompt_template: tone.system_prompt_template,
            is_default: tone.is_default,
          }
        : EMPTY_FORM
    );
    setError(null);
  };

  const handleCreateOrReplace = async (asNew: boolean) => {
    setSaving(true);
    setError(null);
    try {
      if (selectedId && !asNew) {
        await tonesApi.update(selectedId, form);
      } else {
        const created = await tonesApi.create(form);
        setSelectedId(created.id);
      }
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to save tone"));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this tone?")) return;
    await tonesApi.remove(id);
    if (selectedId === id) selectTone(null);
    load();
  };

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Tones</h1>

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <div className="space-y-2">
          {tones.length === 0 && <p className="text-sm text-slate-400">No tones yet — create one below.</p>}
          {tones.map((tone) => (
            <Card key={tone.id} className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <strong className="text-slate-800 dark:text-slate-100">{tone.name}</strong>
                  {tone.is_default && <Badge variant="accent">default</Badge>}
                </div>
                <p className="truncate text-sm text-slate-500 dark:text-slate-400">{tone.description}</p>
              </div>
              <div className="flex shrink-0 gap-1">
                <Button size="sm" onClick={() => selectTone(tone)}>
                  <Pencil className="h-3.5 w-3.5" />
                  Edit
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(tone.id)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400">
          {selectedId ? "Edit tone" : "New tone"}
        </h2>

        <Field label="Name">
          <input
            name="tone-name"
            className={inputClass}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </Field>

        <Field label="Description">
          <input
            name="tone-description"
            className={inputClass}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </Field>

        <Field label="System prompt template">
          <textarea
            name="tone-system-prompt"
            className={inputClass}
            rows={4}
            value={form.system_prompt_template}
            onChange={(e) => setForm({ ...form, system_prompt_template: e.target.value })}
          />
        </Field>

        <label className="mb-3 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input
            name="tone-is-default"
            type="checkbox"
            checked={form.is_default}
            onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
          />
          Set as default tone
        </label>

        {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <div className="flex gap-2">
          <Button
            variant="primary"
            disabled={saving || !form.name || !form.system_prompt_template}
            onClick={() => handleCreateOrReplace(false)}
          >
            {selectedId ? "Save changes" : "Create tone"}
          </Button>
          {selectedId && (
            <Button
              disabled={saving || !form.name || !form.system_prompt_template}
              onClick={() => handleCreateOrReplace(true)}
            >
              Save as new
            </Button>
          )}
          {selectedId && <Button onClick={() => selectTone(null)}>Cancel</Button>}
        </div>
      </Card>
    </div>
  );
}

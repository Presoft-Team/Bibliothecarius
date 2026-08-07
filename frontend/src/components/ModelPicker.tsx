import { useEffect, useState } from "react";
import { llmApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import { inputClass } from "./ui/Field";

interface ModelPickerProps {
  provider: string;
  value: string;
  onChange: (value: string) => void;
  /** Shown as the top option when true — used where an empty value means "use the assistant's default". */
  allowBlank?: boolean;
}

export default function ModelPicker({ provider, value, onChange, allowBlank }: ModelPickerProps) {
  const [models, setModels] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setModels(null);
    setError(null);
    setLoading(true);
    llmApi
      .listModels(provider)
      .then((list) => {
        setModels(list);
        // A required field (allowBlank=false) needs a real value once we know the options —
        // don't leave it pointed at a model that belonged to the previously selected provider.
        if (!allowBlank && list.length > 0 && !list.includes(value)) {
          onChange(list[0]);
        }
      })
      .catch((err) =>
        setError(
          getErrorMessage(
            err,
            `Couldn't list ${provider} models — add an API key in Assistant Settings, or type a model name manually.`
          )
        )
      )
      .finally(() => setLoading(false));
    // Deliberately excludes value/onChange/allowBlank — this should only re-run when the
    // provider itself changes, not on every keystroke into the resulting field.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provider]);

  if (loading) {
    return (
      <input
        name="model"
        className={inputClass}
        value={value}
        disabled
        placeholder="Loading available models…"
        onChange={() => {}}
      />
    );
  }

  if (models && models.length > 0) {
    return (
      <select name="model" className={inputClass} value={value} onChange={(e) => onChange(e.target.value)}>
        {allowBlank && <option value="">Assistant default</option>}
        {models.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div>
      <input
        name="model"
        className={inputClass}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={allowBlank ? "assistant default if blank" : "model name"}
      />
      {error && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}

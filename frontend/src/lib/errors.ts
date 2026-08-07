import axios from "axios";

export function getErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

/** A short, human line for a raw provider error — the full text is still available separately
 * for a "show details" toggle, this is just what's shown by default. */
export function summarizeProviderError(raw: string): string {
  const text = raw.toLowerCase();
  if (text.includes("429") || /rate.?limit|quota/.test(text)) {
    return "The provider is rate-limiting or out of quota — wait a bit and try again.";
  }
  if (text.includes("401") || text.includes("403") || /invalid.*(api.?key|credential)/.test(text)) {
    return "The API key was rejected — check it in Assistant Settings.";
  }
  if (text.includes("404") || /model.*(not found|not supported|is not enabled)/.test(text)) {
    return "The selected model isn't available for this account — try a different one.";
  }
  return "The assistant couldn't respond.";
}

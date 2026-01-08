export function formatIsoDate(value?: string | null): string {
  if (!value) {
    return "N/A";
  }
  return value.replace("T", " ").replace("Z", "").slice(0, 19);
}

export function formatDuration(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) {
    return "N/A";
  }
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
}

export function failureReason({
  error,
  errorCode,
}: {
  error?: string | null;
  errorCode?: string | null;
}): string | null {
  const errorMessage = error ?? "";
  if (
    errorMessage.includes("429") ||
    errorMessage.includes("RESOURCE_EXHAUSTED")
  ) {
    return "Model quota exceeded (429)";
  }
  if (errorCode) {
    return errorCode;
  }
  if (!errorMessage) {
    return null;
  }
  return errorMessage.split("\n")[0];
}

export function extractSourceLabel(
  source?: string | null,
): "manual" | "unknown" {
  if (!source) {
    return "unknown";
  }
  if (source === "manual_agents" || source === "manual_fallback") {
    return "manual";
  }
  return "unknown";
}

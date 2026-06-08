const DEFAULT_BACKEND_API_BASE = "http://localhost:8000";

export function normalizeApiBase(value: string | undefined) {
  return (value?.trim() || DEFAULT_BACKEND_API_BASE).replace(/\/+$/, "");
}

export function backendApiBase() {
  return normalizeApiBase(
    process.env.BACKEND_API_BASE || process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE
  );
}

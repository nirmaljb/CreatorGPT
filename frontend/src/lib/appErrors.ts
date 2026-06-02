export type AppError = {
  code: string;
  message: string;
  scope: string;
  retryable: boolean;
  video_id?: string;
  field?: string;
  retry_after_seconds?: number;
};

export type ParsedApiError = {
  message: string;
  error: AppError | null;
  raw: unknown;
  retryAfterSeconds: number | null;
};

function parseRetryAfter(value: string | null): number | null {
  if (!value) return null;
  const seconds = Number.parseInt(value, 10);
  return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
}

function isAppError(value: unknown): value is AppError {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AppError>;
  return (
    typeof candidate.code === "string" &&
    typeof candidate.message === "string" &&
    typeof candidate.scope === "string" &&
    typeof candidate.retryable === "boolean"
  );
}

export function parseAppErrorPayload(payload: unknown, retryAfterHeader: string | null = null): ParsedApiError {
  const retryAfterSeconds = parseRetryAfter(retryAfterHeader);

  if (payload && typeof payload === "object") {
    const objectPayload = payload as { error?: unknown; detail?: unknown; message?: unknown };
    if (isAppError(objectPayload.error)) {
      return {
        message: objectPayload.error.message,
        error: {
          ...objectPayload.error,
          retry_after_seconds: objectPayload.error.retry_after_seconds ?? retryAfterSeconds ?? undefined
        },
        raw: payload,
        retryAfterSeconds: objectPayload.error.retry_after_seconds ?? retryAfterSeconds
      };
    }
    if (objectPayload.detail && typeof objectPayload.detail === "object") {
      const nested = objectPayload.detail as { error?: unknown };
      if (isAppError(nested.error)) {
        return {
          message: nested.error.message,
          error: {
            ...nested.error,
            retry_after_seconds: nested.error.retry_after_seconds ?? retryAfterSeconds ?? undefined
          },
          raw: payload,
          retryAfterSeconds: nested.error.retry_after_seconds ?? retryAfterSeconds
        };
      }
    }
    if (typeof objectPayload.detail === "string") {
      return { message: objectPayload.detail, error: null, raw: payload, retryAfterSeconds };
    }
    if (typeof objectPayload.message === "string") {
      return { message: objectPayload.message, error: null, raw: payload, retryAfterSeconds };
    }
  }

  if (typeof payload === "string" && payload.trim()) {
    return { message: payload, error: null, raw: payload, retryAfterSeconds };
  }

  return { message: "Request failed", error: null, raw: payload, retryAfterSeconds };
}

export async function parseApiError(response: Response): Promise<ParsedApiError> {
  const retryAfter = response.headers.get("Retry-After");
  const text = await response.text();
  if (!text) {
    return { message: `Request failed: ${response.status}`, error: null, raw: null, retryAfterSeconds: parseRetryAfter(retryAfter) };
  }
  try {
    return parseAppErrorPayload(JSON.parse(text), retryAfter);
  } catch {
    return parseAppErrorPayload(text, retryAfter);
  }
}

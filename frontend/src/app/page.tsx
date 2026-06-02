"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppError, parseApiError, parseAppErrorPayload } from "../lib/appErrors";
import {
  Platform,
  duplicateUrlWarning,
  normalizeVideoInputs,
  sameInputs,
  validateVideoUrl
} from "../lib/urlValidation";

type VideoInputState = {
  video_id: "A" | "B";
  platform: Platform;
  url: string;
};

type VideoMetadata = {
  video_id: "A" | "B";
  url: string;
  platform: string;
  creator: string;
  creator_followers: number;
  creator_followers_available?: boolean;
  views: number;
  views_available?: boolean;
  likes: number;
  likes_available?: boolean;
  comments: number;
  comments_available?: boolean;
  hashtags: string[];
  upload_date: string | null;
  duration_seconds: number;
  engagement_rate: number;
  engagement_rate_available?: boolean;
  ingest_status?: string;
  video_error_message?: string | null;
  video_error?: AppError | null;
  transcript_source?: string;
  chunk_count?: number;
  metadata_cached?: boolean;
  transcript_cached?: boolean;
  has_raw_metadata?: boolean;
};

type Source = {
  type: string;
  video_id: string;
  chunk_index?: number;
  source_tag: string;
};

type ChatMessage = {
  id: string | number;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
};

type StatusResponse = {
  session_id: string;
  status: "processing" | "ready" | "completed" | "failed";
  error_message: string | null;
  error?: AppError | null;
  current_step: string;
  progress_percent: number;
  updated_at: string | null;
  metadata: VideoMetadata[];
};

type RuntimeLimits = {
  max_video_seconds: number;
  max_concurrent_ingestions: number;
  max_chunks_per_video: number;
  max_chat_history_messages: number;
  max_retrieved_chunks: number;
  max_sessions_per_ip_per_hour: number;
};

type OperationPhase = "idle" | "submitting" | "processing" | "completed" | "failed" | "offline" | "chatting";

function normalizeApiBase(value: string | undefined) {
  return (value || "http://localhost:8000").replace(/\/+$/, "");
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_BASE);
const STATUS_REQUEST_TIMEOUT_MS = 7000;
const STALLED_WARNING_MS = 60000;
const NETWORK_MESSAGE =
  "Connection is unavailable or slow. Status polling will keep retrying when the browser is online.";
const DEFAULT_RUNTIME_LIMITS: RuntimeLimits = {
  max_video_seconds: 600,
  max_concurrent_ingestions: 2,
  max_chunks_per_video: 120,
  max_chat_history_messages: 12,
  max_retrieved_chunks: 8,
  max_sessions_per_ip_per_hour: 20
};

function toErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "Request failed";
}

function isNetworkError(error: unknown) {
  return (
    (typeof navigator !== "undefined" && !navigator.onLine) ||
    error instanceof TypeError ||
    (error instanceof DOMException && error.name === "AbortError")
  );
}

function statusPollDelay(progressPercent: number) {
  if (progressPercent < 25) return 2500;
  if (progressPercent < 95) return 8000;
  return 5000;
}

function phaseFromStatus(status: StatusResponse["status"] | "idle", online: boolean): OperationPhase {
  if (!online && status === "processing") return "offline";
  if (status === "ready" || status === "completed") return "completed";
  if (status === "failed") return "failed";
  if (status === "processing") return "processing";
  return online ? "idle" : "offline";
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en", { notation: value >= 1000000 ? "compact" : "standard" }).format(value);
}

function formatMetric(value: number, available = true) {
  return available ? formatNumber(value) : "Unavailable";
}

function formatEngagement(value: number, available = true) {
  return available ? `${value.toFixed(2)}%` : "Unavailable";
}

function formatDuration(seconds: number) {
  const total = Math.max(0, Math.round(seconds || 0));
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

function formatLimitSeconds(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  if (remainder === 0) return `${minutes} min`;
  return `${minutes}m ${remainder}s`;
}

function parseSsePayload(raw: string) {
  const lines = raw.split("\n");
  const eventLine = lines.find((line) => line.startsWith("event:"));
  const dataLines = lines.filter((line) => line.startsWith("data:"));
  const eventName = eventLine?.replace("event:", "").trim();
  const payloadText = dataLines.map((line) => line.replace("data:", "").trim()).join("\n");
  return {
    eventName,
    payload: payloadText ? JSON.parse(payloadText) : {}
  };
}

function VideoCard({ video }: { video?: VideoMetadata }) {
  if (!video) {
    return (
      <section className="video-panel empty">
        <div className="video-label">Video</div>
        <div className="empty-line" />
        <div className="empty-line short" />
      </section>
    );
  }

  const friendlyError = video.video_error?.message || video.video_error_message;

  return (
    <section className="video-panel">
      <div className="video-topline">
        <span className="video-label">Video {video.video_id}</span>
        <span className="platform">{video.platform}</span>
      </div>
      <div className="pipeline-state">
        <span className={`mini-status ${video.ingest_status || "queued"}`}>{video.ingest_status || "queued"}</span>
        <span>{video.transcript_source || "unavailable"}</span>
        <span>{video.chunk_count ?? 0} chunks</span>
        {(video.metadata_cached || video.transcript_cached) && <span>cache</span>}
      </div>
      {friendlyError && <p className="video-error">{friendlyError}</p>}
      <h2>{video.creator || "unknown"}</h2>
      <dl className="metrics">
        <div>
          <dt>Views</dt>
          <dd>{formatMetric(video.views, video.views_available ?? true)}</dd>
        </div>
        <div>
          <dt>Likes</dt>
          <dd>{formatMetric(video.likes, video.likes_available ?? true)}</dd>
        </div>
        <div>
          <dt>Comments</dt>
          <dd>{formatMetric(video.comments, video.comments_available ?? true)}</dd>
        </div>
        <div>
          <dt>Followers</dt>
          <dd>
            {formatMetric(video.creator_followers, video.creator_followers_available ?? Boolean(video.creator_followers))}
          </dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>{formatDuration(video.duration_seconds)}</dd>
        </div>
        <div>
          <dt>Engagement</dt>
          <dd>{formatEngagement(video.engagement_rate, video.engagement_rate_available ?? true)}</dd>
        </div>
      </dl>
      <div className="tags">{video.hashtags.slice(0, 6).map((tag) => <span key={tag}>{tag}</span>)}</div>
    </section>
  );
}

export default function Home() {
  const [videoInputs, setVideoInputs] = useState<VideoInputState[]>([
    { video_id: "A", platform: "youtube", url: "" },
    { video_id: "B", platform: "instagram", url: "" }
  ]);
  const [touched, setTouched] = useState<Record<"A" | "B", boolean>>({ A: false, B: false });
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [submittedInputs, setSubmittedInputs] = useState<VideoInputState[] | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse["status"] | "idle">("idle");
  const [operationPhase, setOperationPhase] = useState<OperationPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata[]>([]);
  const [currentStep, setCurrentStep] = useState("Idle");
  const [progressPercent, setProgressPercent] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [networkMessage, setNetworkMessage] = useState<string | null>(null);
  const [stalledMessage, setStalledMessage] = useState<string | null>(null);
  const [retryUntil, setRetryUntil] = useState<number | null>(null);
  const [retryCountdown, setRetryCountdown] = useState<number | null>(null);
  const [limits, setLimits] = useState<RuntimeLimits>(DEFAULT_RUNTIME_LIMITS);

  const activeSessionRef = useRef<string | null>(null);
  const requestSeqRef = useRef(0);
  const chatRunRef = useRef(0);
  const chatAbortRef = useRef<AbortController | null>(null);
  const statusRef = useRef<StatusResponse["status"] | "idle">("idle");
  const lastStatusSignatureRef = useRef<string | null>(null);
  const lastMovementAtRef = useRef(Date.now());

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const normalizedInputs = useMemo(() => normalizeVideoInputs(videoInputs), [videoInputs]);
  const validations = useMemo(
    () =>
      videoInputs.reduce(
        (acc, video) => ({ ...acc, [video.video_id]: validateVideoUrl(video.platform, video.url) }),
        {} as Record<"A" | "B", ReturnType<typeof validateVideoUrl>>
      ),
    [videoInputs]
  );
  const hasValidationErrors = Object.values(validations).some((validation) => Boolean(validation.error));
  const duplicateWarning = useMemo(() => duplicateUrlWarning(videoInputs), [videoInputs]);
  const pendingInputChanges = status === "completed" && submittedInputs && !sameInputs(normalizedInputs, submittedInputs);
  const videoA = useMemo(() => metadata.find((item) => item.video_id === "A"), [metadata]);
  const videoB = useMemo(() => metadata.find((item) => item.video_id === "B"), [metadata]);
  const isReady = status === "ready" || status === "completed";
  const inputsLocked = operationPhase === "submitting" || status === "processing";
  const rateLimitActive = retryCountdown !== null && retryCountdown > 0;
  const canIngest = !hasValidationErrors && !inputsLocked && !isStreaming && isOnline && !rateLimitActive;
  const canChat = isReady && !isStreaming && isOnline;
  const sourceDisplayLimit = limits.max_retrieved_chunks;
  const displayPhase = operationPhase === "chatting" ? "chatting" : operationPhase;

  function updateVideoInput(videoId: "A" | "B", patch: Partial<VideoInputState>) {
    setVideoInputs((current) =>
      current.map((video) => (video.video_id === videoId ? { ...video, ...patch } : video))
    );
  }

  function markTouched(videoId: "A" | "B") {
    setTouched((current) => ({ ...current, [videoId]: true }));
  }

  function setRetryCountdownFromSeconds(seconds: number | null) {
    if (!seconds) return;
    const until = Date.now() + seconds * 1000;
    setRetryUntil(until);
    setRetryCountdown(seconds);
  }

  function phaseForCurrentStatus(online = isOnline) {
    return phaseFromStatus(statusRef.current, online);
  }

  function logStatusErrors(data: StatusResponse) {
    const videoErrors = (data.metadata || [])
      .filter((video) => video.video_error || video.video_error_message)
      .map((video) => ({
        video_id: video.video_id,
        structured: video.video_error,
        raw: video.video_error_message
      }));
    if (data.error || data.error_message || videoErrors.length > 0) {
      console.warn("Status returned structured/raw error context", {
        session_id: data.session_id,
        structured: data.error,
        raw: data.error_message,
        videoErrors
      });
    }
  }

  const handleRequestError = useCallback((exception: unknown, fallback: string) => {
    if (isNetworkError(exception)) {
      console.warn("Network/API request failed; request will retry when appropriate", exception);
      setNetworkMessage(NETWORK_MESSAGE);
      return;
    }
    setError(toErrorMessage(exception) || fallback);
  }, []);

  const loadStatus = useCallback(
    async (id: string, signal?: AbortSignal) => {
      console.info("Loading status", { sessionId: id });
      const response = await fetch(`${API_BASE}/status/${id}`, { cache: "no-store", signal });
      if (!response.ok) {
        throw new Error((await parseApiError(response)).message);
      }
      const data: StatusResponse = await response.json();
      if (activeSessionRef.current !== id) {
        console.info("Ignoring stale status response", { sessionId: id, activeSessionId: activeSessionRef.current });
        return data;
      }

      const signature = `${data.current_step}|${data.progress_percent}|${data.updated_at || ""}`;
      if (data.status === "processing") {
        if (signature !== lastStatusSignatureRef.current) {
          lastStatusSignatureRef.current = signature;
          lastMovementAtRef.current = Date.now();
          setStalledMessage(null);
        } else if (Date.now() - lastMovementAtRef.current >= STALLED_WARNING_MS) {
          setStalledMessage("No progress update for over 60 seconds. Still checking backend status.");
        }
      } else {
        setStalledMessage(null);
      }

      console.info("Status loaded", {
        sessionId: id,
        status: data.status,
        step: data.current_step,
        progress: data.progress_percent,
        metadataCount: data.metadata?.length || 0
      });
      logStatusErrors(data);
      setNetworkMessage(null);
      setStatus(data.status);
      setOperationPhase(phaseFromStatus(data.status, isOnline));
      setMetadata(data.metadata || []);
      setCurrentStep(data.current_step || data.status);
      setProgressPercent(data.progress_percent || 0);
      setError(data.error?.message || data.error_message);
      return data;
    },
    [isOnline]
  );

  const loadMessages = useCallback(async (id: string) => {
    const response = await fetch(`${API_BASE}/messages/${id}`, { cache: "no-store" });
    if (!response.ok || activeSessionRef.current !== id) return;
    const data = await response.json();
    setMessages(
      (data.messages || []).map((item: ChatMessage) => ({
        ...item,
        sources: item.sources || []
      }))
    );
  }, []);

  const loadRuntimeConfig = useCallback(async () => {
    const response = await fetch(`${API_BASE}/config`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Config request failed: ${response.status}`);
    }
    const data = await response.json();
    if (data.limits) {
      setLimits({ ...DEFAULT_RUNTIME_LIMITS, ...data.limits });
    }
  }, []);

  useEffect(() => {
    window.localStorage.removeItem("creator_session_id");
    setIsOnline(window.navigator.onLine);
    setOperationPhase(window.navigator.onLine ? "idle" : "offline");
    loadRuntimeConfig().catch((exc) => {
      console.warn("Runtime config request failed; using frontend fallback limits", exc);
    });

    function handleOffline() {
      console.warn("Browser reported offline; status polling paused");
      setIsOnline(false);
      setOperationPhase((current) => (current === "processing" ? "offline" : current));
      setNetworkMessage(NETWORK_MESSAGE);
    }

    function handleOnline() {
      console.info("Browser reported online; status polling will resume");
      setIsOnline(true);
      setOperationPhase((current) => (current === "offline" ? phaseFromStatus(statusRef.current, true) : current));
      setNetworkMessage(null);
    }

    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [loadRuntimeConfig]);

  useEffect(() => {
    if (!retryUntil) {
      setRetryCountdown(null);
      return;
    }

    const updateCountdown = () => {
      const remaining = Math.max(0, Math.ceil((retryUntil - Date.now()) / 1000));
      setRetryCountdown(remaining);
      if (remaining <= 0) {
        setRetryUntil(null);
      }
    };

    updateCountdown();
    const interval = window.setInterval(updateCountdown, 1000);
    return () => window.clearInterval(interval);
  }, [retryUntil]);

  useEffect(() => {
    if (!sessionId || !isOnline) return;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), STATUS_REQUEST_TIMEOUT_MS);
    loadStatus(sessionId, controller.signal)
      .catch((exc) => handleRequestError(exc, "Status request failed"))
      .finally(() => window.clearTimeout(timeout));
    loadMessages(sessionId).catch(() => undefined);
    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [handleRequestError, isOnline, loadMessages, loadStatus, sessionId]);

  useEffect(() => {
    if (!sessionId || status !== "processing" || !isOnline) return;
    let stopped = false;
    let pollTimeout: number | undefined;
    let controller: AbortController | undefined;

    const poll = async () => {
      controller = new AbortController();
      const requestTimeout = window.setTimeout(() => controller?.abort(), STATUS_REQUEST_TIMEOUT_MS);
      let nextProgress = progressPercent;
      let keepPolling = true;
      try {
        const data = await loadStatus(sessionId, controller.signal);
        nextProgress = data.progress_percent || 0;
        keepPolling = data.status === "processing";
      } catch (exc) {
        handleRequestError(exc, "Status request failed");
      } finally {
        window.clearTimeout(requestTimeout);
      }

      if (!stopped && activeSessionRef.current === sessionId && keepPolling) {
        pollTimeout = window.setTimeout(poll, statusPollDelay(nextProgress));
      }
    };

    pollTimeout = window.setTimeout(() => {
      void poll();
    }, statusPollDelay(progressPercent));

    return () => {
      stopped = true;
      controller?.abort();
      if (pollTimeout) window.clearTimeout(pollTimeout);
    };
  }, [handleRequestError, isOnline, loadStatus, sessionId, status, progressPercent]);

  async function handleIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitAttempted(true);
    setTouched({ A: true, B: true });
    if (hasValidationErrors || isStreaming || inputsLocked) return;
    if (!isOnline) {
      setNetworkMessage("Connection is unavailable. Reconnect before starting a new ingest.");
      return;
    }
    if (rateLimitActive) return;

    const requestId = requestSeqRef.current + 1;
    requestSeqRef.current = requestId;
    setOperationPhase("submitting");
    setError(null);
    setNetworkMessage(null);
    setStalledMessage(null);

    try {
      const response = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: normalizedInputs.map((video) => ({
            video_id: video.video_id,
            platform: video.platform,
            url: video.url
          }))
        })
      });
      if (requestSeqRef.current !== requestId) return;

      if (!response.ok) {
        const parsed = await parseApiError(response);
        console.warn("Ingest request failed", parsed.raw);
        setRetryCountdownFromSeconds(parsed.retryAfterSeconds);
        setError(parsed.message);
        setOperationPhase(phaseForCurrentStatus());
        return;
      }

      const data = await response.json();
      if (requestSeqRef.current !== requestId) return;

      activeSessionRef.current = data.session_id;
      lastStatusSignatureRef.current = null;
      lastMovementAtRef.current = Date.now();
      setSubmittedInputs(normalizedInputs);
      setSessionId(data.session_id);
      setMetadata([]);
      setMessages([]);
      setCurrentStep("Queued");
      setProgressPercent(0);
      setStatus("processing");
      setOperationPhase("processing");
      setError(null);
    } catch (exc) {
      if (requestSeqRef.current !== requestId) return;
      handleRequestError(exc, "Ingest request failed");
      setOperationPhase(phaseForCurrentStatus());
    }
  }

  function updateDraft(id: string, content: string, sources: Source[]) {
    setMessages((current) =>
      current.map((item) => (item.id === id ? { ...item, content, sources } : item))
    );
  }

  async function handleChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sessionId || !chatInput.trim() || !canChat) return;

    const chatRunId = chatRunRef.current + 1;
    chatRunRef.current = chatRunId;
    const controller = new AbortController();
    chatAbortRef.current = controller;
    const question = chatInput.trim();
    const draftId = `draft-${Date.now()}`;
    setChatInput("");
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", content: question, sources: [] },
      { id: draftId, role: "assistant", content: "", sources: [] }
    ]);
    setIsStreaming(true);
    setOperationPhase("chatting");
    setError(null);
    setNetworkMessage(null);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: question }),
        signal: controller.signal
      });
      if (!response.ok || !response.body) {
        const parsed = await parseApiError(response);
        throw new Error(parsed.message);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let content = "";
      let sources: Source[] = [];
      let streamFailed = false;

      readLoop: while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (chatRunRef.current !== chatRunId || activeSessionRef.current !== sessionId) return;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const raw of events) {
          const { eventName, payload } = parseSsePayload(raw);
          if (eventName === "sources") {
            sources = payload.sources || [];
            updateDraft(draftId, content, sources);
          }
          if (eventName === "token") {
            content += payload.token || "";
            updateDraft(draftId, content, sources);
          }
          if (eventName === "error") {
            const parsed = parseAppErrorPayload(payload);
            console.warn("Chat stream failed", parsed.raw);
            streamFailed = true;
            setError(parsed.message);
            updateDraft(draftId, content || parsed.message, sources);
            break readLoop;
          }
        }
      }

      if (!streamFailed && activeSessionRef.current === sessionId) {
        await loadMessages(sessionId);
      }
    } catch (exc) {
      if (controller.signal.aborted) return;
      const message = toErrorMessage(exc) || "Chat request failed";
      updateDraft(draftId, message, []);
      handleRequestError(exc, "Chat request failed");
    } finally {
      if (chatRunRef.current === chatRunId) {
        chatAbortRef.current = null;
        setIsStreaming(false);
        setOperationPhase(phaseForCurrentStatus());
      }
    }
  }

  function handleLocalReset() {
    if (status === "processing") {
      const confirmed = window.confirm(
        "This clears only this browser view. Backend ingestion may continue until it reaches a terminal state."
      );
      if (!confirmed) return;
    }

    requestSeqRef.current += 1;
    chatRunRef.current += 1;
    chatAbortRef.current?.abort();
    chatAbortRef.current = null;
    activeSessionRef.current = null;
    lastStatusSignatureRef.current = null;
    window.localStorage.removeItem("creator_session_id");
    setSessionId(null);
    setSubmittedInputs(null);
    setStatus("idle");
    setOperationPhase(isOnline ? "idle" : "offline");
    setError(null);
    setNetworkMessage(null);
    setStalledMessage(null);
    setMetadata([]);
    setMessages([]);
    setCurrentStep("Idle");
    setProgressPercent(0);
    setChatInput("");
    setIsStreaming(false);
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Creator RAG Comparator</p>
          <h1>Compare two creator videos</h1>
        </div>
        <div className="status-block">
          <div className={`status ${status} ${displayPhase}`}>{displayPhase}</div>
          {status === "processing" && (
            <div className="progress-summary">
              <div className="progress-label">
                <span>{currentStep}</span>
                <span>{progressPercent}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
              </div>
            </div>
          )}
        </div>
      </header>

      <form className="ingest" onSubmit={handleIngest}>
        {videoInputs.map((video) => {
          const validation = validations[video.video_id];
          const showError = (touched[video.video_id] || submitAttempted) && validation.error;
          return (
            <label key={video.video_id}>
              Video {video.video_id}
              <div className="url-control">
                <select
                  value={video.platform}
                  disabled={inputsLocked}
                  onBlur={() => markTouched(video.video_id)}
                  onChange={(event) => {
                    markTouched(video.video_id);
                    updateVideoInput(video.video_id, { platform: event.target.value as Platform });
                  }}
                >
                  <option value="youtube">YouTube</option>
                  <option value="instagram">Instagram</option>
                </select>
                <input
                  value={video.url}
                  disabled={inputsLocked}
                  onBlur={() => markTouched(video.video_id)}
                  onChange={(event) => {
                    markTouched(video.video_id);
                    updateVideoInput(video.video_id, { url: event.target.value });
                  }}
                  placeholder={
                    video.platform === "youtube"
                      ? "https://youtube.com/watch?v=..."
                      : "https://www.instagram.com/reel/..."
                  }
                />
              </div>
              {showError && <span className="field-error">{validation.error}</span>}
            </label>
          );
        })}
        <button type="submit" disabled={!canIngest}>
          {operationPhase === "submitting"
            ? "Submitting"
            : status === "failed"
              ? "Retry ingest"
              : pendingInputChanges
                ? "Start new"
                : "Start ingest"}
        </button>
      </form>

      {(duplicateWarning || pendingInputChanges || rateLimitActive) && (
        <div className="warning-stack">
          {duplicateWarning && <p className="warning">{duplicateWarning}</p>}
          {pendingInputChanges && <p className="warning">Inputs changed. Chat remains tied to the completed session.</p>}
          {rateLimitActive && <p className="warning">Retry available in about {retryCountdown} seconds.</p>}
        </div>
      )}

      <section className="limit-strip" aria-label="Runtime limits">
        <span>Whisper cap {formatLimitSeconds(limits.max_video_seconds)}</span>
        <span>{limits.max_concurrent_ingestions} concurrent ingest</span>
        <span>{limits.max_chunks_per_video} chunks/video</span>
        <span>{limits.max_chat_history_messages} history messages</span>
        <span>{limits.max_retrieved_chunks} retrieved chunks</span>
        <span>{limits.max_sessions_per_ip_per_hour} sessions/IP/hour</span>
      </section>

      <div className="session-row">
        {sessionId && <p className="session">Session: {sessionId}</p>}
        {sessionId && (
          <button className="secondary-action" type="button" onClick={handleLocalReset}>
            {status === "processing" ? "Local reset" : "Reset view"}
          </button>
        )}
      </div>
      {networkMessage && <p className="network-alert">{networkMessage}</p>}
      {stalledMessage && <p className="network-alert">{stalledMessage}</p>}
      {error && <p className="error">{error}</p>}

      <section className="workspace">
        <div className="videos">
          <VideoCard video={videoA} />
          <VideoCard video={videoB} />
        </div>

        <section className="chat-panel">
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty-chat">
                Ask about engagement rate, hooks, creators, follower counts, or improvements once ingestion is ready.
              </div>
            )}
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="role">{message.role}</div>
                <p>{message.content || (message.role === "assistant" ? "Streaming..." : "")}</p>
                {message.sources?.length > 0 && (
                  <div className="sources">
                    {message.sources.slice(0, sourceDisplayLimit).map((source) => (
                      <span key={`${message.id}-${source.source_tag}`}>{source.source_tag}</span>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>

          <form className="chat-input" onSubmit={handleChat}>
            <input
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              disabled={!canChat}
              placeholder={
                isReady
                  ? isOnline
                    ? "Ask about the two videos..."
                    : "Reconnect before chat"
                  : "Ingest must finish before chat"
              }
            />
            <button type="submit" disabled={!canChat || !chatInput.trim()}>
              Send
            </button>
          </form>
        </section>
      </section>
    </main>
  );
}

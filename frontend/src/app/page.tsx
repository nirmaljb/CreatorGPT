"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Platform = "youtube" | "instagram";

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
  current_step: string;
  progress_percent: number;
  updated_at: string | null;
  metadata: VideoMetadata[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const NETWORK_MESSAGE =
  "Connection is unavailable. Status polling will resume when the browser is online and the API is reachable.";

function toErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "Request failed";
}

function isNetworkError(error: unknown) {
  return (typeof navigator !== "undefined" && !navigator.onLine) || error instanceof TypeError;
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
      {video.video_error_message && <p className="video-error">{video.video_error_message}</p>}
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
          <dd>{formatMetric(video.creator_followers, video.creator_followers_available ?? Boolean(video.creator_followers))}</dd>
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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse["status"] | "idle">("idle");
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata[]>([]);
  const [currentStep, setCurrentStep] = useState("Idle");
  const [progressPercent, setProgressPercent] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [networkMessage, setNetworkMessage] = useState<string | null>(null);

  const videoA = useMemo(() => metadata.find((item) => item.video_id === "A"), [metadata]);
  const videoB = useMemo(() => metadata.find((item) => item.video_id === "B"), [metadata]);
  const isReady = status === "ready" || status === "completed";
  const canIngest = videoInputs.every((video) => video.url.trim().length > 0) && status !== "processing" && isOnline;
  const canChat = isReady && !isStreaming && isOnline;

  function updateVideoInput(videoId: "A" | "B", patch: Partial<VideoInputState>) {
    setVideoInputs((current) =>
      current.map((video) => (video.video_id === videoId ? { ...video, ...patch } : video))
    );
  }

  const handleRequestError = useCallback((exception: unknown, fallback: string) => {
    if (isNetworkError(exception)) {
      console.warn("Network/API request failed; polling is paused until connectivity returns", exception);
      setNetworkMessage(NETWORK_MESSAGE);
      return;
    }
    setError(toErrorMessage(exception) || fallback);
  }, []);

  const loadStatus = useCallback(async (id: string) => {
    const response = await fetch(`${API_BASE}/status/${id}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Status request failed: ${response.status}`);
    }
    const data: StatusResponse = await response.json();
    setNetworkMessage(null);
    setStatus(data.status);
    setMetadata(data.metadata || []);
    setCurrentStep(data.current_step || data.status);
    setProgressPercent(data.progress_percent || 0);
    setError(data.error_message);
    return data;
  }, []);

  const loadMessages = useCallback(async (id: string) => {
    const response = await fetch(`${API_BASE}/messages/${id}`, { cache: "no-store" });
    if (!response.ok) return;
    const data = await response.json();
    setMessages(
      (data.messages || []).map((item: ChatMessage) => ({
        ...item,
        sources: item.sources || []
      }))
    );
  }, []);

  useEffect(() => {
    window.localStorage.removeItem("creator_session_id");
    setIsOnline(window.navigator.onLine);

    function handleOffline() {
      console.warn("Browser reported offline; status polling paused");
      setIsOnline(false);
      setNetworkMessage(NETWORK_MESSAGE);
    }

    function handleOnline() {
      console.info("Browser reported online; status polling will resume");
      setIsOnline(true);
      setNetworkMessage(null);
    }

    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, []);

  useEffect(() => {
    if (!sessionId || !isOnline) return;
    loadStatus(sessionId).catch((exc) => handleRequestError(exc, "Status request failed"));
    loadMessages(sessionId).catch(() => undefined);
  }, [handleRequestError, isOnline, loadMessages, loadStatus, sessionId]);

  useEffect(() => {
    if (!sessionId || status !== "processing" || !isOnline) return;
    const delay = progressPercent < 25 ? 2500 : progressPercent < 95 ? 8000 : 5000;
    const timeout = window.setTimeout(() => {
      loadStatus(sessionId).catch((exc) => handleRequestError(exc, "Status request failed"));
    }, delay);
    return () => window.clearTimeout(timeout);
  }, [handleRequestError, isOnline, loadStatus, sessionId, status, progressPercent]);

  async function handleIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isOnline) {
      setNetworkMessage("Connection is unavailable. Reconnect before starting a new ingest.");
      return;
    }
    setError(null);
    setNetworkMessage(null);
    setMetadata([]);
    setMessages([]);
    setCurrentStep("Queued");
    setProgressPercent(0);
    setStatus("processing");

    try {
      const response = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: videoInputs.map((video) => ({
            video_id: video.video_id,
            platform: video.platform,
            url: video.url.trim()
          }))
        })
      });
      if (!response.ok) {
        setStatus("idle");
        setError(await response.text());
        return;
      }
      const data = await response.json();
      setSessionId(data.session_id);
    } catch (exc) {
      setStatus("idle");
      handleRequestError(exc, "Ingest request failed");
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

    const question = chatInput.trim();
    const draftId = `draft-${Date.now()}`;
    setChatInput("");
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", content: question, sources: [] },
      { id: draftId, role: "assistant", content: "", sources: [] }
    ]);
    setIsStreaming(true);
    setError(null);
    setNetworkMessage(null);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: question })
      });
      if (!response.ok || !response.body) {
        throw new Error(await response.text());
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let content = "";
      let sources: Source[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const raw of events) {
          const lines = raw.split("\n");
          const eventLine = lines.find((line) => line.startsWith("event:"));
          const dataLine = lines.find((line) => line.startsWith("data:"));
          const eventName = eventLine?.replace("event:", "").trim();
          const payload = dataLine ? JSON.parse(dataLine.replace("data:", "").trim()) : {};

          if (eventName === "sources") {
            sources = payload.sources || [];
            updateDraft(draftId, content, sources);
          }
          if (eventName === "token") {
            content += payload.token || "";
            updateDraft(draftId, content, sources);
          }
          if (eventName === "error") {
            setError(payload.message || "Chat failed");
          }
        }
      }
      await loadMessages(sessionId);
    } catch (exc) {
      handleRequestError(exc, "Chat request failed");
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Creator RAG Comparator</p>
          <h1>Compare two creator videos</h1>
        </div>
        <div className="status-block">
          <div className={`status ${status}`}>{status}</div>
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
        {videoInputs.map((video) => (
          <label key={video.video_id}>
            Video {video.video_id}
            <div className="url-control">
              <select
                value={video.platform}
                onChange={(event) => updateVideoInput(video.video_id, { platform: event.target.value as Platform })}
              >
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
              </select>
              <input
                value={video.url}
                onChange={(event) => updateVideoInput(video.video_id, { url: event.target.value })}
                placeholder={
                  video.platform === "youtube"
                    ? "https://youtube.com/watch?v=..."
                    : "https://www.instagram.com/reel/..."
                }
              />
            </div>
          </label>
        ))}
        <button type="submit" disabled={!canIngest}>
          Start ingest
        </button>
      </form>

      {sessionId && <p className="session">Session: {sessionId}</p>}
      {networkMessage && <p className="network-alert">{networkMessage}</p>}
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
                    {message.sources.slice(0, 10).map((source) => (
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

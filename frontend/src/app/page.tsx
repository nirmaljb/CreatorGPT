"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type ConnectionStatus = "connected" | "incomplete_scopes" | "reconnect_required" | "disconnected";

type MeResponse = {
  authenticated: boolean;
  user: {
    id: string;
    email: string | null;
    email_verified: boolean;
    name: string | null;
    avatar_url: string | null;
  } | null;
  youtube: {
    connection_status: ConnectionStatus;
    granted_scopes: string[];
    missing_scopes: string[];
    reconnect_needed: boolean;
    last_verified_at: string | null;
  };
  csrf_token: string | null;
};

const scopeRows = [
  {
    label: "Google identity",
    detail: "Confirms who is signed in with name, email, and profile identity.",
    access: "Identity"
  },
  {
    label: "YouTube channel access",
    detail: "Reads channel and video metadata for videos you own.",
    access: "Read only"
  },
  {
    label: "YouTube Analytics",
    detail: "Reads private performance metrics needed for channel-relative diagnosis.",
    access: "Private metrics"
  }
];

const guardrails = [
  {
    title: "Read-only scope",
    detail: "No upload, edit, delete, caption-management, or channel-management permission."
  },
  {
    title: "No money metrics",
    detail: "Revenue and monetary analytics scopes are not requested for this MVP."
  },
  {
    title: "Server-side tokens",
    detail: "Refresh tokens stay off the browser and are encrypted before storage."
  }
];

const readinessSteps = [
  {
    stage: "01",
    title: "Connect",
    detail: "Verify the creator account with read-only Google and YouTube access."
  },
  {
    stage: "02",
    title: "Select",
    detail: "Choose one owned long-form upload for diagnosis."
  },
  {
    stage: "03",
    title: "Diagnose",
    detail: "Compare against channel baseline evidence before naming a bottleneck."
  }
];

function normalizeApiBase(value: string | undefined) {
  return (value || "http://localhost:8000").replace(/\/+$/, "");
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_BASE);

function statusLabel(status: ConnectionStatus) {
  if (status === "connected") return "Connected";
  if (status === "incomplete_scopes") return "Access incomplete";
  if (status === "reconnect_required") return "Reconnect needed";
  return "Not connected";
}

function statusCopy(me: MeResponse | null) {
  if (!me?.authenticated) return "Connect YouTube to start with private creator analytics.";
  if (me.youtube.connection_status === "connected") return "Your account is ready for channel selection.";
  if (me.youtube.connection_status === "incomplete_scopes") {
    return "Some required read-only scopes were not granted. Reconnect to continue.";
  }
  if (me.youtube.connection_status === "reconnect_required") {
    return "The connection needs a fresh consent grant before analysis can start.";
  }
  return "You are signed in, but YouTube is not connected.";
}

function actionLabel(me: MeResponse | null, loading: boolean) {
  if (loading) return "Continue with Google";
  if (me?.youtube.reconnect_needed) return "Reconnect YouTube";
  if (me?.youtube.connection_status === "connected") return "Review YouTube access";
  return "Connect YouTube";
}

export default function Home() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const connectUrl = useMemo(() => `${API_BASE}/auth/google/start`, []);

  const loadMe = useCallback(async () => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/me`, {
        credentials: "include",
        cache: "no-store"
      });
      if (!response.ok) throw new Error("Connection status is unavailable.");
      setMe((await response.json()) as MeResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection status is unavailable.");
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  const connectionStatus = me?.youtube.connection_status ?? "disconnected";
  const missingScopes = me?.youtube.missing_scopes ?? [];
  const grantedScopes = me?.youtube.granted_scopes ?? [];
  const lastVerified = useMemo(() => {
    const rawValue = me?.youtube.last_verified_at;
    if (!rawValue) return null;

    const date = new Date(rawValue);
    if (Number.isNaN(date.getTime())) return null;

    return {
      dateTime: rawValue,
      label: new Intl.DateTimeFormat(undefined, {
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        month: "short"
      }).format(date)
    };
  }, [me?.youtube.last_verified_at]);

  return (
    <main className="creator-shell" id="main-content">
      <header className="creator-topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            YD
          </span>
          <div>
            <p className="eyebrow">YouTube diagnosis concierge</p>
            <p className="product-name">Signal Room</p>
          </div>
        </div>
        <nav className="utility-nav" aria-label="Secondary navigation">
          <Link className="text-link" href="/faq">
            FAQ
          </Link>
        </nav>
      </header>

      <section className="hero-panel" aria-labelledby="connect-title">
        <div className="hero-copy">
          <p className="eyebrow">Creator-owned evidence</p>
          <h1 id="connect-title">Diagnose the video with your channel&apos;s real baseline.</h1>
          <p>
            Start with OAuth so the report can use private analytics, owned-video metadata, and a baseline that belongs
            to the creator instead of public guesswork.
          </p>
        </div>

        <ol className="readiness-rail" aria-label="Analysis readiness">
          {readinessSteps.map((step) => (
            <li key={step.stage}>
              <span className="step-index">{step.stage}</span>
              <div>
                <h2>{step.title}</h2>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="connect-grid" aria-labelledby="connection-heading">
        <div className="connect-primary">
          <div className={`status-card ${connectionStatus}`} aria-busy={loading} aria-live="polite">
            <div className="connection-state">
              <span className={`state-dot ${connectionStatus}`} aria-hidden="true" />
              <span>{loading ? "Checking connection…" : statusLabel(connectionStatus)}</span>
            </div>
            <h2 id="connection-heading">Connection readiness</h2>
            <p className="connect-copy">{loading ? "Checking your server-side session…" : statusCopy(me)}</p>
            {lastVerified && (
              <p className="last-verified">
                Last verified <time dateTime={lastVerified.dateTime}>{lastVerified.label}</time>
              </p>
            )}
          </div>

          {me?.user && (
            <div className="identity-strip" aria-label="Signed-in identity">
              <span className="avatar-mark" aria-hidden="true">
                {(me.user.name || me.user.email || "G").slice(0, 1).toUpperCase()}
              </span>
              <div>
                <strong>{me.user.name || me.user.email || "Google account"}</strong>
                {me.user.email && <span>{me.user.email}</span>}
              </div>
            </div>
          )}

          {error && (
            <p className="status-message error" role="alert">
              {error}
            </p>
          )}
          {missingScopes.length > 0 && (
            <div className="status-message warn" role="status">
              <strong>Missing required access</strong>
              <span>{missingScopes.join(", ")}</span>
            </div>
          )}

          <a className="connect-button" href={connectUrl} aria-describedby="connect-help">
            <span>{actionLabel(me, loading)}</span>
            <span className="button-arrow" aria-hidden="true">
              -&gt;
            </span>
          </a>
          <p className="action-help" id="connect-help">
            Opens Google consent for the narrow read-only scopes listed here.
          </p>
        </div>

        <aside className="scope-panel" aria-labelledby="scope-heading">
          <p className="panel-kicker">Requested access</p>
          <h2 id="scope-heading">Only the evidence needed for diagnosis</h2>
          <div className="scope-list">
            {scopeRows.map((scope) => (
              <div className="scope-row" key={scope.label}>
                <div>
                  <h3>{scope.label}</h3>
                  <p>{scope.detail}</p>
                </div>
                <span>{scope.access}</span>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="guardrail-band" aria-label="Access guardrails">
        {guardrails.map((item) => (
          <article key={item.title}>
            <h2>{item.title}</h2>
            <p>{item.detail}</p>
          </article>
        ))}
      </section>

      {grantedScopes.length > 0 && (
        <section className="scope-audit" aria-label="Granted scopes">
          <div>
            <p className="panel-kicker">Granted scopes recorded</p>
            <p>The backend stores the exact granted scope list and never returns OAuth tokens to this page.</p>
          </div>
          <ul>
            {grantedScopes.map((scope) => (
              <li key={scope}>{scope}</li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

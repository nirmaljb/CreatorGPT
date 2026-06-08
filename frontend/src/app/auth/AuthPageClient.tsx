"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  connectionLabel,
  fetchCurrentSession,
  formatSessionDate,
  hasCompleteYouTubeAccess,
  type MeResponse
} from "../../lib/session";

const accessRows = [
  {
    label: "Google identity",
    detail: "Name, profile identity, verified email when available.",
    scope: "openid / email / profile"
  },
  {
    label: "YouTube channel and videos",
    detail: "Channel identity and metadata for uploads owned by the connected creator.",
    scope: "youtube.readonly"
  },
  {
    label: "YouTube Analytics",
    detail: "Private performance signals needed for channel-relative diagnosis.",
    scope: "yt-analytics.readonly"
  }
];

const neverRows = [
  "Upload, edit, delete, or manage videos",
  "Manage captions or request caption-management scopes",
  "Read revenue or monetary analytics",
  "Expose OAuth tokens to the browser",
  "Continuously sync the whole channel"
];

function consentCopy(me: MeResponse | null, loading: boolean) {
  if (loading) return "Checking your current session…";
  if (!me?.authenticated) return "Continue with Google to grant narrow read-only access.";
  if (hasCompleteYouTubeAccess(me)) return "You are connected. Opening the workspace…";
  if (me.youtube.connection_status === "incomplete_scopes") {
    return "Some required read-only scopes are missing. Continue with Google to repair access.";
  }
  if (me.youtube.connection_status === "reconnect_required") {
    return "This connection needs a fresh consent grant before diagnosis can start.";
  }
  return "You are signed in, but YouTube is not connected yet.";
}

export default function AuthPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSession = useCallback(async () => {
    setError(null);
    try {
      setMe(await fetchCurrentSession());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection status is unavailable.");
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (searchParams.get("auth") !== "unavailable") return;
    setError(searchParams.get("reason") || "Google OAuth start is unavailable.");
  }, [searchParams]);

  useEffect(() => {
    if (!loading && hasCompleteYouTubeAccess(me)) {
      const timeout = window.setTimeout(() => router.replace("/app"), 700);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [loading, me, router]);

  const connectionStatus = me?.youtube.connection_status ?? "disconnected";
  const lastVerified = useMemo(() => formatSessionDate(me?.youtube.last_verified_at ?? null), [me]);
  const missingScopes = me?.youtube.missing_scopes ?? [];

  return (
    <main className="auth-shell" id="main-content">
      <header className="simple-topbar">
        <Link className="brand-link" href="/" aria-label="Candor home">
          <span className="brand-mark" aria-hidden="true">
            C
          </span>
          <span>Candor</span>
        </Link>
        <nav className="utility-nav" aria-label="Secondary navigation">
          <Link className="text-link" href="/faq">
            FAQ
          </Link>
        </nav>
      </header>

      <section className="auth-intro" aria-labelledby="auth-title">
        <p className="eyebrow">Read-only consent</p>
        <h1 id="auth-title">Connect YouTube without handing Candor the controls.</h1>
        <p>
          Candor needs private creator analytics to compare one owned long-form upload against your own channel
          baseline. The consent request is narrow and read-only.
        </p>
      </section>

      <section className="auth-layout" aria-labelledby="consent-title">
        <div className={`consent-panel state-${connectionStatus}`} aria-busy={loading} aria-live="polite">
          <div className="status-line">
            <span className={`state-dot ${connectionStatus}`} aria-hidden="true" />
            <span>{loading ? "Checking access…" : connectionLabel(connectionStatus)}</span>
          </div>
          <h2 id="consent-title">Google and YouTube permission</h2>
          <p>{consentCopy(me, loading)}</p>

          {me?.user && (
            <div className="identity-strip" aria-label="Signed-in Google identity">
              <span className="avatar-mark" aria-hidden="true">
                {(me.user.name || me.user.email || "G").slice(0, 1).toUpperCase()}
              </span>
              <div>
                <strong>{me.user.name || me.user.email || "Google account"}</strong>
                {me.user.email && <span>{me.user.email}</span>}
              </div>
            </div>
          )}

          {lastVerified && (
            <p className="metadata-line">
              Last verified <time dateTime={lastVerified.dateTime}>{lastVerified.label}</time>
            </p>
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

          <a className="primary-action" href="/auth/google/start">
            Continue with Google
          </a>
          <p className="fine-print">
            If YouTube Analytics data is delayed later, Candor will ask before sending any per-run notification email.
          </p>
        </div>

        <div className="permission-list" aria-label="Requested access">
          {accessRows.map((row) => (
            <article className="permission-row" key={row.label}>
              <div>
                <h2>{row.label}</h2>
                <p>{row.detail}</p>
              </div>
              <span>{row.scope}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="never-panel" aria-labelledby="never-title">
        <div>
          <p className="eyebrow">Never requested</p>
          <h2 id="never-title">Candor does not ask for creator control.</h2>
        </div>
        <ul>
          {neverRows.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}

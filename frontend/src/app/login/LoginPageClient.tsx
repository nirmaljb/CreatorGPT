"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  connectionLabel,
  fetchCurrentSession,
  hasCompleteYouTubeAccess,
  type MeResponse
} from "../../lib/session";

const trustRows = [
  {
    label: "Identity",
    detail: "Google account identity and verified email when available."
  },
  {
    label: "Ownership",
    detail: "YouTube channel and upload metadata for videos you own."
  },
  {
    label: "Diagnosis",
    detail: "Private analytics needed to compare one video against your baseline."
  }
];

function loginCopy(me: MeResponse | null, loading: boolean) {
  if (loading) return "Checking your current session…";
  if (hasCompleteYouTubeAccess(me)) return "You are connected. Opening the workspace…";
  if (me?.authenticated) return "Your Google session needs YouTube access before diagnosis can start.";
  return "Use Google to continue into Candor.";
}

export default function LoginPageClient() {
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
      const timeout = window.setTimeout(() => router.replace("/app"), 500);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [loading, me, router]);

  const connectionStatus = me?.youtube.connection_status ?? "disconnected";
  const missingScopes = me?.youtube.missing_scopes ?? [];
  const statusLabel = useMemo(
    () => (loading ? "Checking access…" : connectionLabel(connectionStatus)),
    [connectionStatus, loading]
  );

  return (
    <main className="login-shell" id="main-content">
      <header className="simple-topbar">
        <Link className="brand-link" href="/" aria-label="Candor home">
          <span className="brand-mark" aria-hidden="true">
            C
          </span>
          <span>Candor</span>
        </Link>
        <nav className="utility-nav" aria-label="Secondary navigation">
          <Link className="text-link" href="/auth">
            Access details
          </Link>
          <Link className="text-link" href="/faq">
            FAQ
          </Link>
        </nav>
      </header>

      <section className="login-layout" aria-labelledby="login-title">
        <div className={`login-panel state-${connectionStatus}`} aria-busy={loading} aria-live="polite">
          <p className="eyebrow">Creator login</p>
          <h1 id="login-title">Log in to diagnose your next YouTube decision.</h1>
          <p>{loginCopy(me, loading)}</p>

          <div className="status-line">
            <span className={`state-dot ${connectionStatus}`} aria-hidden="true" />
            <span>{statusLabel}</span>
          </div>

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

          <div className="login-actions">
            <a className="primary-action" href="/auth/google/start?returnTo=/login">
              Continue with Google
            </a>
            <Link className="secondary-action" href="/auth">
              Review read-only access
            </Link>
          </div>
        </div>

        <aside className="login-ledger" aria-label="Login access summary">
          <p className="eyebrow">Read-only boundary</p>
          <h2>Sign in without giving Candor creator controls.</h2>
          <div className="login-ledger-list">
            {trustRows.map((row) => (
              <article className="login-ledger-row" key={row.label}>
                <span>{row.label}</span>
                <p>{row.detail}</p>
              </article>
            ))}
          </div>
          <p className="fine-print">
            Candor never asks to upload, edit, delete, manage captions, or read revenue metrics.
          </p>
        </aside>
      </section>
    </main>
  );
}

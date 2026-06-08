"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  connectionLabel,
  fetchCurrentSession,
  formatSessionDate,
  hasCompleteYouTubeAccess,
  type MeResponse
} from "../../lib/session";

const evidenceRows = [
  {
    label: "Selected video snapshot",
    state: "waiting",
    detail: "Owned long-form upload metadata and publish window."
  },
  {
    label: "Channel baseline",
    state: "waiting",
    detail: "At least 5 comparable prior long-form uploads."
  },
  {
    label: "Retention and analytics",
    state: "waiting",
    detail: "Private first-7-completed-days performance signals."
  },
  {
    label: "Transcript and structure",
    state: "optional",
    detail: "Hook, payoff, pacing, and mapped timestamp evidence."
  },
  {
    label: "Comments and audience signals",
    state: "optional",
    detail: "Timestamp reactions and representative audience language."
  }
];

const contextChips = ["Felt slow early", "Audience seemed confused", "Views stopped expanding", "Not sure yet"];

function AccountMenu({ me }: { me: MeResponse }) {
  const name = me.user?.name || me.user?.email || "Google account";
  const verifiedEmail = me.user?.email_verified && me.user?.email ? me.user.email : "Verified email unavailable";

  return (
    <details className="account-menu">
      <summary>
        <span className="avatar-mark" aria-hidden="true">
          {name.slice(0, 1).toUpperCase()}
        </span>
        <span>{name}</span>
      </summary>
      <div className="account-menu-panel">
        <p>
          <strong>Notification email</strong>
          <span>{verifiedEmail}</span>
        </p>
        <Link href="/faq">FAQ</Link>
        <button type="button" disabled>
          Settings
        </button>
      </div>
    </details>
  );
}

function NeedsAccess({ me, error }: { me: MeResponse | null; error: string | null }) {
  const status = me?.youtube.connection_status ?? "disconnected";

  return (
    <main className="app-shell" id="main-content">
      <header className="app-topbar">
        <Link className="brand-link" href="/" aria-label="Candor home">
          <span className="brand-mark" aria-hidden="true">
            C
          </span>
          <span>Candor</span>
        </Link>
        <span className="workflow-pill">Video selection</span>
      </header>
      <section className="access-gate" aria-labelledby="access-title">
        <p className="eyebrow">Workspace access</p>
        <h1 id="access-title">Connect YouTube before choosing a video.</h1>
        <p>
          Candor only diagnoses videos owned by the connected creator. Finish read-only access before the upload list
          opens.
        </p>
        <div className="status-line">
          <span className={`state-dot ${status}`} aria-hidden="true" />
          <span>{connectionLabel(status)}</span>
        </div>
        {error && (
          <p className="status-message error" role="alert">
            {error}
          </p>
        )}
        <Link className="primary-action" href="/login">
          Log in with Google
        </Link>
      </section>
    </main>
  );
}

export default function AppPageClient() {
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

  const lastVerified = useMemo(() => formatSessionDate(me?.youtube.last_verified_at ?? null), [me]);

  if (loading) {
    return (
      <main className="app-shell" id="main-content" aria-busy="true">
        <header className="app-topbar">
          <Link className="brand-link" href="/" aria-label="Candor home">
            <span className="brand-mark" aria-hidden="true">
              C
            </span>
            <span>Candor</span>
          </Link>
          <span className="workflow-pill">Checking session…</span>
        </header>
        <section className="access-gate">
          <p className="eyebrow">Workspace access</p>
          <h1>Checking YouTube access…</h1>
        </section>
      </main>
    );
  }

  if (!hasCompleteYouTubeAccess(me)) {
    return <NeedsAccess me={me} error={error} />;
  }

  return (
    <main className="app-shell" id="main-content">
      <header className="app-topbar">
        <Link className="brand-link" href="/" aria-label="Candor home">
          <span className="brand-mark" aria-hidden="true">
            C
          </span>
          <span>Candor</span>
        </Link>
        <span className="workflow-pill">Video selection</span>
        {me && <AccountMenu me={me} />}
      </header>

      <section className="workspace-hero" aria-labelledby="workspace-title">
        <div>
          <p className="eyebrow">Connected workspace</p>
          <h1 id="workspace-title">Choose one owned long-form upload.</h1>
          <p>
            The first report should answer why a video underperformed, not ask you to inspect a dashboard first.
          </p>
        </div>
        <div className="channel-chip" aria-label="Current connection">
          <span className="state-dot connected" aria-hidden="true" />
          <div>
            <strong>{me?.user?.name || me?.user?.email || "Google account connected"}</strong>
            {lastVerified && (
              <span>
                Verified <time dateTime={lastVerified.dateTime}>{lastVerified.label}</time>
              </span>
            )}
          </div>
        </div>
      </section>

      <section className="selection-layout" aria-label="Video diagnosis setup">
        <div className="upload-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Recent uploads</p>
              <h2>Owned video list</h2>
            </div>
            <details className="filter-menu">
              <summary>Filter</summary>
              <div>
                <label>
                  Search title
                  <input name="upload-search" type="search" placeholder="Paste or search title…" autoComplete="off" />
                </label>
                <label>
                  Owned URL fallback
                  <input name="owned-url" type="url" inputMode="url" placeholder="https://youtu.be/…" autoComplete="off" />
                </label>
              </div>
            </details>
          </div>

          <div className="empty-upload-state" role="status">
            <div className="thumbnail-placeholder" aria-hidden="true" />
            <div>
              <h3>No owned uploads are available from this session yet.</h3>
              <p>
                Candor will show a row list here after channel lookup is connected: title, thumbnail, publish date,
                duration, public views, eligibility, and one Diagnose action.
              </p>
            </div>
          </div>
        </div>

        <aside className="context-panel" aria-labelledby="context-title">
          <p className="eyebrow">Optional context</p>
          <h2 id="context-title">What felt wrong?</h2>
          <div className="chip-row" aria-label="Optional context chips">
            {contextChips.map((chip) => (
              <button key={chip} type="button">
                {chip}
              </button>
            ))}
          </div>
          <details className="manual-context">
            <summary>Add a note</summary>
            <label>
              Creator-provided context
              <textarea
                name="creator-context"
                placeholder="Add what you expected, what changed, or what you noticed…"
                autoComplete="off"
              />
            </label>
          </details>
          <button className="secondary-action" type="button" disabled>
            Start diagnosis
          </button>
        </aside>
      </section>

      <section className="evidence-progress" aria-labelledby="evidence-title">
        <div>
          <p className="eyebrow">Evidence collection</p>
          <h2 id="evidence-title">The report starts only after core evidence is ready.</h2>
        </div>
        <div className="evidence-list">
          {evidenceRows.map((row) => (
            <article className={`evidence-row state-${row.state}`} key={row.label}>
              <span>{row.state}</span>
              <div>
                <h3>{row.label}</h3>
                <p>{row.detail}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

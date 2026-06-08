import Link from "next/link";

const reportEvidence = [
  {
    label: "Known",
    detail: "First 7 completed days, owned upload metadata, 8 comparable long-form videos."
  },
  {
    label: "Suggested",
    detail: "Retention appears to drop before the video delivers the promised payoff."
  },
  {
    label: "Not known yet",
    detail: "No CTR or impressions context, so Candor should not blame packaging."
  }
];

const steps = [
  {
    title: "Connect read-only YouTube",
    detail: "Candor uses OAuth because reliable diagnosis needs private creator analytics, not public guesswork."
  },
  {
    title: "Pick one owned long-form video",
    detail: "The workspace stays focused on the video you want to understand instead of opening a dashboard."
  },
  {
    title: "Get the clearest report evidence supports",
    detail: "If the data is incomplete, Candor says what is missing and asks only targeted follow-up questions."
  }
];

const notRows = [
  "No clickbait title generator",
  "No thumbnail gimmick tool",
  "No copying bigger creators",
  "No fake certainty",
  "No generic AI coach"
];

export default function Home() {
  return (
    <main className="landing-shell" id="main-content">
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

      <section className="landing-hero" aria-labelledby="hero-title">
        <p className="eyebrow">YouTube diagnosis for serious creators</p>
        <h1 id="hero-title">Why did this video underperform?</h1>
        <p>
          Candor connects to your YouTube channel, compares one owned long-form upload against your own baseline, and
          gives the clearest diagnosis the evidence can support.
        </p>
        <div className="hero-actions">
          <Link className="primary-action" href="/login">
            Connect YouTube
          </Link>
          <Link className="text-link" href="/faq">
            Read the trust FAQ
          </Link>
        </div>
      </section>

      <section className="report-preview-band" aria-labelledby="preview-title">
        <div className="section-heading">
          <p className="eyebrow">Report preview</p>
          <h2 id="preview-title">The answer starts with evidence, not a score.</h2>
        </div>

        <article className="report-preview" aria-label="Sample Candor report preview">
          <div className="report-preview-header">
            <div>
              <span className="metadata-label">Sample report</span>
              <h3>Likely bottleneck: Hook expectation gap</h3>
            </div>
            <span className="confidence-tag">Medium evidence</span>
          </div>
          <p className="report-answer">
            Based on available signals, the video likely lost momentum before viewers reached the promised payoff.
            Packaging is not the leading explanation without click-opportunity evidence.
          </p>
          <div className="evidence-preview-list">
            {reportEvidence.map((row) => (
              <div className="evidence-preview-row" key={row.label}>
                <span>{row.label}</span>
                <p>{row.detail}</p>
              </div>
            ))}
          </div>
          <div className="timestamp-strip" aria-label="Cited evidence examples">
            <span>[Retention: 00:15-00:30]</span>
            <span>[Baseline: 8 prior long-form videos]</span>
          </div>
        </article>
      </section>

      <section className="process-band" aria-labelledby="process-title">
        <div className="section-heading">
          <p className="eyebrow">How it works</p>
          <h2 id="process-title">One job, one video, one report.</h2>
        </div>
        <ol className="process-list">
          {steps.map((step, index) => (
            <li key={step.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="anti-gimmick-band" aria-labelledby="not-title">
        <div className="section-heading">
          <p className="eyebrow">What Candor is not</p>
          <h2 id="not-title">Better diagnosis without creator imitation.</h2>
        </div>
        <ul>
          {notRows.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <footer className="trust-footer">
        <div>
          <strong>Read-only by design.</strong>
          <p>
            Candor will not upload, edit, delete, manage captions, read revenue metrics, or expose tokens to the
            browser.
          </p>
        </div>
        <Link className="text-link" href="/auth">
          Review access
        </Link>
      </footer>
    </main>
  );
}

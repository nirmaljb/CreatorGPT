import Link from "next/link";

const faqs = [
  {
    question: "Why does Candor need OAuth?",
    answer:
      "Public video data cannot show the private analytics needed for a reliable diagnosis. OAuth lets Candor compare one owned upload against your own channel baseline with read-only access."
  },
  {
    question: "What data does Candor read?",
    answer:
      "Candor asks for Google identity, YouTube channel/video metadata, and YouTube Analytics signals. It uses that evidence to build a report for the selected video."
  },
  {
    question: "What will Candor never do?",
    answer:
      "Candor will not upload, edit, delete, manage captions, request revenue metrics, expose tokens to the browser, or continuously sync the whole channel."
  },
  {
    question: "Why compare against my channel instead of bigger creators?",
    answer:
      "Large channels usually have different audiences, budgets, formats, history, and distribution context. Your own baseline is a better default because it respects your audience and style."
  },
  {
    question: "Why might Candor say we do not know yet?",
    answer:
      "A primary bottleneck needs enough evidence. If core analytics, baseline history, ownership checks, or content signals are missing, Candor should show hypotheses and targeted asks instead of forcing certainty."
  },
  {
    question: "Why are Shorts excluded?",
    answer:
      "The MVP diagnosis is built for long-form videos. Shorts use different viewing patterns, baselines, and assumptions, so Candor should not apply long-form rules to them."
  },
  {
    question: "Does Candor generate titles or thumbnails?",
    answer:
      "No. Candor may give evidence-based follow-through after a report, but it is not a clickbait title generator, thumbnail generator, or tool for copying larger creators."
  },
  {
    question: "How do I disconnect or delete analysis data?",
    answer:
      "Those trust controls belong in creator settings as the product matures. Disconnect should stop future access, while delete-analysis-data should remove stored reports and evidence."
  }
];

export const metadata = {
  title: "FAQ | Candor",
  description: "Candor trust, OAuth, evidence, and product-boundary questions."
};

export default function FaqPage() {
  return (
    <main className="faq-shell" id="main-content">
      <header className="simple-topbar">
        <Link className="brand-link" href="/" aria-label="Candor home">
          <span className="brand-mark" aria-hidden="true">
            C
          </span>
          <span>Candor</span>
        </Link>
        <nav className="utility-nav" aria-label="Secondary navigation">
          <Link className="text-link" href="/login">
            Connect YouTube
          </Link>
        </nav>
      </header>

      <section className="faq-hero" aria-labelledby="faq-title">
        <p className="eyebrow">Trust FAQ</p>
        <h1 id="faq-title">How Candor uses YouTube evidence.</h1>
        <p>
          Candor is built around a narrow read-only trust boundary, channel-relative diagnosis, and honest uncertainty
          when evidence is incomplete.
        </p>
      </section>

      <section className="faq-list" aria-label="Frequently asked questions">
        {faqs.map((item) => (
          <article className="faq-item" key={item.question}>
            <h2>{item.question}</h2>
            <p>{item.answer}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

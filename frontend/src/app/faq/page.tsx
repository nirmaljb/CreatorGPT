import Link from "next/link";

const faqs = [
  {
    question: "Why does the product not compare creators to big channels by default?",
    answer: [
      "The product is designed to help creators understand their own videos, audience, taste, and channel patterns. Larger channels often have different audiences, budgets, formats, publishing history, and distribution context, so using them as the default benchmark can push creators toward imitation instead of useful learning.",
      "The default comparison should be the creator's own channel baseline and the selected video's actual evidence. If a creator does not have enough channel history, the product should produce a learning-mode report instead of pretending a big-channel comparison is a reliable diagnosis.",
      "Creators can add reference videos later, but those references should be treated as study material, not standards they must copy. The product should extract transferable mechanics, tradeoffs, and risks of imitation while preserving the creator's own intent and style."
    ]
  }
];

export default function FaqPage() {
  return (
    <main className="faq-shell" id="main-content">
      <header className="faq-header">
        <Link className="back-link" href="/">
          Back to connection
        </Link>
        <p className="eyebrow">Product FAQ</p>
        <h1>How this product thinks about creator growth</h1>
        <p className="faq-intro">
          The product is built around evidence, creator intent, and channel-specific learning rather than defaulting to
          imitation of larger channels.
        </p>
      </header>

      <section className="faq-list" aria-label="Frequently asked questions">
        {faqs.map((item) => (
          <article className="faq-item" key={item.question}>
            <h2>{item.question}</h2>
            {item.answer.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </article>
        ))}
      </section>
    </main>
  );
}

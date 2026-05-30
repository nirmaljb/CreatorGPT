import "./globals.css";

export const metadata = {
  title: "Creator Video RAG",
  description: "Compare creator videos with metadata, transcripts, and cited RAG answers."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

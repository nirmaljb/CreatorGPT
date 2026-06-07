import "./globals.css";

export const metadata = {
  title: "YouTube Diagnosis Concierge",
  description: "Connect YouTube for creator-owned video performance diagnosis."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}

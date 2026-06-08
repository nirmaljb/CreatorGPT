import { Suspense } from "react";

import AuthPageClient from "./AuthPageClient";

export const metadata = {
  title: "Connect YouTube | Candor",
  description: "Review Candor's read-only Google and YouTube access before connecting."
};

export default function AuthPage() {
  return (
    <Suspense fallback={<main className="auth-shell" id="main-content" aria-busy="true" />}>
      <AuthPageClient />
    </Suspense>
  );
}

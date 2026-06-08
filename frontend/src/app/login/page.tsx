import { Suspense } from "react";

import LoginPageClient from "./LoginPageClient";

export const metadata = {
  title: "Log In | Candor",
  description: "Log in to Candor with read-only Google and YouTube access."
};

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="login-shell" id="main-content" aria-busy="true" />}>
      <LoginPageClient />
    </Suspense>
  );
}

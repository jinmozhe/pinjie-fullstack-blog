import type { Metadata } from "next";
import { AuthForm } from "@/features/auth/AuthForm";
import { fetchRegistrationState, fetchSiteProfile } from "@/lib/api/server";

export const metadata: Metadata = { title: "登录", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const [registrationState, siteProfile] = await Promise.all([fetchRegistrationState(), fetchSiteProfile()]);
  return <AuthForm mode="login" registrationEnabled={registrationState === "enabled"} siteProfile={siteProfile} />;
}

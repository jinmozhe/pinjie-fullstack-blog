import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthForm } from "@/features/auth/AuthForm";
import { SiteBrand } from "@/features/site";
import { fetchRegistrationState, fetchSiteProfile } from "@/lib/api/server";

export const metadata: Metadata = { title: "注册", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function RegisterPage() {
  const [registrationState, siteProfile] = await Promise.all([fetchRegistrationState(), fetchSiteProfile()]);
  if (registrationState === "disabled") redirect("/login");
  if (registrationState === "unavailable") {
    return (
      <main className="auth-shell">
        <section className="auth-panel" aria-labelledby="registration-unavailable-title">
          <SiteBrand profile={siteProfile} />
          <div className="auth-heading">
            <p className="kicker">ACCOUNT ACCESS</p>
            <h1 id="registration-unavailable-title">注册暂不可用</h1>
            <p>当前无法确认注册服务状态，请稍后重试或返回登录。</p>
          </div>
          <Link className="primary-action compact" href="/login">返回登录</Link>
        </section>
        <aside className="auth-context" aria-hidden="true"><div><p className="kicker">SECURE BY DEFAULT</p><h2>访问能力始终由服务端确认</h2><p>系统不会在状态未知时开放账户注册。</p></div></aside>
      </main>
    );
  }
  return <AuthForm mode="register" siteProfile={siteProfile} />;
}

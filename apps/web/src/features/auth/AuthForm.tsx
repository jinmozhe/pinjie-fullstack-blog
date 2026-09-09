"use client";

import type { FormEvent } from "react";
import type { SiteProfileRead } from "@pinjie/api-client";
import { ArrowRight, LockKeyhole, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { webAuthApi } from "./api";
import { ApiError, errorMessage } from "@/lib/api/http";
import { SiteBrand } from "@/features/site";

export function AuthForm({
  mode,
  registrationEnabled = true,
  siteProfile,
}: {
  mode: "login" | "register";
  registrationEnabled?: boolean;
  siteProfile?: SiteProfileRead;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();
  const [retryAfter, setRetryAfter] = useState<string>();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(undefined);
    const form = new FormData(event.currentTarget);
    const username = String(form.get("username") ?? "");
    const password = String(form.get("password") ?? "");
    try {
      if (mode === "login") await webAuthApi.login(username, password);
      else await webAuthApi.register({
        username,
        password,
        display_name: String(form.get("display_name") ?? "") || null,
        email: String(form.get("email") ?? "") || null,
      });
      router.replace("/account");
      router.refresh();
    } catch (caught) {
      setError(errorMessage(caught));
      if (caught instanceof ApiError) setRetryAfter(caught.retryAfter);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel" aria-labelledby="auth-title">
        <SiteBrand profile={siteProfile} />
        <div className="auth-heading">
          <p className="kicker">{mode === "login" ? "ACCOUNT ACCESS" : "CREATE ACCOUNT"}</p>
          <h1 id="auth-title">{mode === "login" ? "欢迎回来" : "创建你的账户"}</h1>
          <p>{mode === "login" ? "进入用户中心管理资料和登录设备。" : "用户名将作为默认登录标识，邮箱当前仅作联系资料。"}</p>
        </div>
        {error && <div className="form-alert" role="alert">{error}{retryAfter ? `，请在 ${retryAfter} 秒后重试` : ""}</div>}
        <form className="auth-form" onSubmit={submit}>
          <label htmlFor="username">用户名</label>
          <div className="input-wrap"><UserRound aria-hidden="true" size={18} /><input id="username" name="username" autoComplete="username" minLength={3} maxLength={50} required /></div>
          {mode === "register" && <>
            <label htmlFor="display_name">显示名称 <span>选填</span></label>
            <input id="display_name" name="display_name" maxLength={100} />
            <label htmlFor="email">邮箱 <span>选填，尚未验证</span></label>
            <input id="email" name="email" type="email" maxLength={320} autoComplete="email" />
          </>}
          <label htmlFor="password">密码</label>
          <div className="input-wrap"><LockKeyhole aria-hidden="true" size={18} /><input id="password" name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "register" ? 6 : 1} maxLength={64} required /></div>
          {mode === "register" && <p className="field-hint">至少 6 个字符，最多 64 个字符。</p>}
          <button className="primary-action" disabled={pending} type="submit">{pending ? "正在提交" : mode === "login" ? "登录" : "注册并登录"}<ArrowRight aria-hidden="true" size={18} /></button>
        </form>
        {(mode === "register" || registrationEnabled) && <p className="auth-switch">{mode === "login" ? "还没有账户？" : "已经有账户？"}<Link href={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "立即注册" : "返回登录"}</Link></p>}
      </section>
      <aside className="auth-context" aria-label="账户安全说明">
        <div><p className="kicker">SECURE SESSION</p><h2>凭据留在浏览器的安全边界内</h2><p>访问令牌和刷新令牌由 HttpOnly Cookie 管理。用户中心不会把令牌写入页面、URL 或浏览器持久化存储。</p></div>
      </aside>
    </main>
  );
}

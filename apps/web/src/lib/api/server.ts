import {
  getSiteProfileApiV1SystemSiteProfileGet,
  getSystemCapabilitiesApiV1SystemCapabilitiesGet,
  getSystemStatusApiV1SystemStatusGet,
} from "@pinjie/api-client";
import type { SiteProfileRead, SystemStatus, UserPrincipalOut } from "@pinjie/api-client";
import { createClient } from "@pinjie/api-client/client";
import { cookies } from "next/headers";
import { cache } from "react";

import { DEFAULT_SITE_PROFILE } from "@/features/site";

const WEB_COOKIE_NAMES = new Set(["pinjie_blog_web_access", "pinjie_blog_web_refresh", "pinjie_blog_web_csrf"]);

export const fetchSiteProfile = cache(async (): Promise<SiteProfileRead> => {
  const baseURL = process.env.BACKEND_INTERNAL_URL;
  if (!baseURL) return DEFAULT_SITE_PROFILE;
  const serverClient = createClient({ baseURL });
  try {
    const result = await getSiteProfileApiV1SystemSiteProfileGet({
      client: serverClient,
      throwOnError: true,
    });
    return result.data.data;
  } catch {
    return DEFAULT_SITE_PROFILE;
  }
});

function webCookies(cookieHeader: string): string {
  return cookieHeader
    .split(";")
    .map((item) => item.trim())
    .filter((item) => WEB_COOKIE_NAMES.has(item.split("=", 1)[0] ?? ""))
    .join("; ");
}

export async function fetchInitialSystemStatus(): Promise<SystemStatus> {
  const baseURL = process.env.BACKEND_INTERNAL_URL;
  if (!baseURL) {
    return { status: "unavailable" };
  }
  const serverClient = createClient({ baseURL });
  try {
    const result = await getSystemStatusApiV1SystemStatusGet({ client: serverClient, throwOnError: true });
    return result.data.data;
  } catch {
    return { status: "unavailable" };
  }
}

export type RegistrationState = "enabled" | "disabled" | "unavailable";

export async function fetchRegistrationState(): Promise<RegistrationState> {
  const baseURL = process.env.BACKEND_INTERNAL_URL;
  if (!baseURL) return "unavailable";

  const serverClient = createClient({ baseURL });
  try {
    const result = await getSystemCapabilitiesApiV1SystemCapabilitiesGet({
      client: serverClient,
      throwOnError: true,
    });
    return result.data.data.registration_enabled ? "enabled" : "disabled";
  } catch {
    return "unavailable";
  }
}

export class ServerAuthError extends Error {
  constructor(public readonly status: number) {
    super("Server authentication request failed");
  }
}

export type ServerAuthenticationState = "authenticated" | "anonymous" | "unavailable";

export async function fetchCurrentUser(): Promise<UserPrincipalOut> {
  const baseURL = process.env.BACKEND_INTERNAL_URL;
  if (!baseURL) throw new ServerAuthError(503);
  const cookieStore = await cookies();
  const response = await fetch(new URL("/api/v1/users/me", baseURL), {
    cache: "no-store",
    headers: { accept: "application/json", cookie: webCookies(cookieStore.toString()) },
  });
  if (!response.ok) throw new ServerAuthError(response.status);
  const payload = (await response.json()) as { data: UserPrincipalOut };
  return payload.data;
}

export async function fetchAuthenticationState(): Promise<ServerAuthenticationState> {
  try {
    await fetchCurrentUser();
    return "authenticated";
  } catch (error) {
    if (error instanceof ServerAuthError && error.status === 401) return "anonymous";
    return "unavailable";
  }
}

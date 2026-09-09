import type { ActionResult, PageResultSessionRead, RefreshSessionOut, UserAuthSessionOut, UserPrincipalOut, UserRegisterIn, UserUpdateIn } from "@pinjie/api-client";

import { webRequest } from "@/lib/api/http";

export const webAuthApi = {
  login: (username: string, password: string) => webRequest<UserAuthSessionOut>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }, false),
  register: (input: UserRegisterIn) => webRequest<UserAuthSessionOut>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(input) }, false),
  refresh: () => webRequest<RefreshSessionOut>("/api/v1/auth/refresh", { method: "POST" }, false),
  me: (signal?: globalThis.AbortSignal) => webRequest<UserPrincipalOut>("/api/v1/users/me", {}, true, signal),
  update: (input: UserUpdateIn) => webRequest<UserPrincipalOut>("/api/v1/users/me", { method: "PATCH", body: JSON.stringify(input) }),
  updateAvatar: (assetId: string | null) => webRequest<UserPrincipalOut>("/api/v1/users/me/avatar", { method: "PUT", body: JSON.stringify({ asset_id: assetId }) }),
  changePassword: (currentPassword: string, newPassword: string) => webRequest<RefreshSessionOut>("/api/v1/users/me/password", { method: "POST", body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }),
  sessions: (signal?: globalThis.AbortSignal) => webRequest<PageResultSessionRead>("/api/v1/users/me/sessions?page=1&page_size=100", {}, true, signal),
  revokeSession: (id: string) => webRequest<ActionResult>(`/api/v1/users/me/sessions/${id}`, { method: "DELETE" }),
  revokeOthers: () => webRequest<ActionResult>("/api/v1/users/me/sessions/revoke-others", { method: "POST" }),
  logout: () => webRequest<ActionResult>("/api/v1/auth/logout", { method: "POST" }, false),
  deleteAccount: (currentPassword: string) => webRequest<ActionResult>("/api/v1/users/me", { method: "DELETE", body: JSON.stringify({ current_password: currentPassword }) }),
};

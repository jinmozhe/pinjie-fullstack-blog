import type { AdminRead } from "@pinjie/api-client";
import { createContext, useContext } from "react";

export const AdminContext = createContext<AdminRead | null>(null);

export function useCurrentAdmin(): AdminRead {
  const admin = useContext(AdminContext);
  if (!admin) throw new Error("AdminContext is unavailable");
  return admin;
}
export function canAccess(admin: AdminRead, permission: string): boolean {
  return admin.is_superuser || admin.permissions.includes(permission);
}

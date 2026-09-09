import type { SystemOverviewRead } from "@pinjie/api-client";

import { adminApi } from "@/lib/api/admin";

export async function fetchSystemOverview(): Promise<SystemOverviewRead> {
  return adminApi.systemOverview();
}

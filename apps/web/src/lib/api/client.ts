import { getSystemStatusApiV1SystemStatusGet } from "@pinjie/api-client";
import type { SystemStatus } from "@pinjie/api-client";
import { client } from "@pinjie/api-client/client.gen";

client.setConfig({ baseURL: typeof window === "undefined" ? "http://localhost:8000" : window.location.origin });

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const result = await getSystemStatusApiV1SystemStatusGet({ client, throwOnError: true });
  return result.data.data;
}

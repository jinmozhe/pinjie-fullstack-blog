"use client";

import { useState } from "react";
import type { SystemStatus } from "@pinjie/api-client";

import { fetchSystemStatus } from "@/lib/api/client";

type Props = { initialStatus: SystemStatus };

export function SystemStatusCard({ initialStatus }: Props) {
  const [status, setStatus] = useState(initialStatus.status);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function retry() {
    setLoading(true);
    setError(false);
    try {
      const nextStatus = await fetchSystemStatus();
      setStatus(nextStatus.status);
    } catch {
      setError(true);
      setStatus("unavailable");
    } finally {
      setLoading(false);
    }
  }

  const available = status === "available" && !error;
  return (
    <section className="status-panel" aria-labelledby="status-heading">
      <div className="status-panel__header">
        <div>
          <p className="kicker">RUNTIME STATUS</p>
          <h2 id="status-heading">系统运行状态</h2>
        </div>
        <span className={`status-pill ${available ? "status-pill--ok" : "status-pill--error"}`}>
          {available ? "可用" : "不可用"}
        </span>
      </div>
      <p className="status-panel__copy">
        这里显示当前后端基础服务是否可用，不包含具体派生业务状态。
      </p>
      {error ? <p className="status-message status-message--error" role="alert">后端服务暂不可用，请稍后重试。</p> : null}
      <button className="status-action" type="button" onClick={retry} disabled={loading}>
        {loading ? "正在检查" : "重新检查"}
      </button>
    </section>
  );
}

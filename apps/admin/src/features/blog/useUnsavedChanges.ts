import { history } from "@umijs/max";
import { useEffect, useRef } from "react";

export function useUnsavedChanges(dirty: boolean, busy: boolean) {
  const bypass = useRef(false);
  const latest = useRef({ dirty, busy });
  latest.current = { dirty, busy };
  useEffect(() => {
    const unblock = history.block((transition) => {
      if (latest.current.busy && !bypass.current) return;
      if (!bypass.current && latest.current.dirty && !window.confirm("还有未保存的内容，离开后会丢失。确定离开吗？")) return;
      unblock();
      transition.retry();
    });
    const beforeUnload = (event: globalThis.BeforeUnloadEvent) => {
      if (!bypass.current && (latest.current.dirty || latest.current.busy)) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => { unblock(); window.removeEventListener("beforeunload", beforeUnload); };
  }, []);
  return () => { bypass.current = true; };
}

import type { ComponentProps } from "react";

// Full document navigation rechecks public visibility instead of reusing an RSC history payload.
export function ReadingLink(props: ComponentProps<"a"> & { href: string }) {
  return <a {...props} />;
}

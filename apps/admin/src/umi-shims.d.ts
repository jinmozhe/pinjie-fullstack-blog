export {};

declare module "@umijs/max" {
  import type { ComponentType, ReactNode } from "react";
  export const history: {
    location: { pathname: string; search: string; hash: string };
    replace: (path: string) => void;
    push: (path: string) => void;
    block: (blocker: (transition: { retry: () => void }) => void) => () => void;
  };
  export function useParams<T extends Record<string, string | undefined>>(): Readonly<Partial<T>>;
  export const Link: ComponentType<{ to: string; children?: ReactNode }>;
}

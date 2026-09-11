import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<"input">
>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    ref={ref}
    className={cn(
      "flex min-h-11 w-full min-w-0 rounded-control border border-input bg-card px-4 py-2 text-base placeholder:text-muted-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:bg-muted disabled:text-muted-foreground",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

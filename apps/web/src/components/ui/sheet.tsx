"use client";

import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "./button";

export const Sheet = Dialog.Root;
export const SheetTrigger = Dialog.Trigger;
export const SheetClose = Dialog.Close;
export const SheetTitle = Dialog.Title;
export const SheetDescription = Dialog.Description;

export const SheetContent = React.forwardRef<
  React.ComponentRef<typeof Dialog.Content>,
  React.ComponentPropsWithoutRef<typeof Dialog.Content>
>(({ className, children, ...props }, ref) => (
  <Dialog.Portal>
    <Dialog.Overlay className="fixed inset-0 z-[var(--z-overlay)] bg-black/40 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0 duration-panel" />
    <Dialog.Content
      ref={ref}
      className={cn(
        "fixed inset-y-0 left-0 z-[var(--z-dialog)] flex h-dvh w-[min(320px,calc(100vw-32px))] flex-col overflow-y-auto bg-sidebar p-5 pt-[max(24px,env(safe-area-inset-top))] pb-[max(24px,env(safe-area-inset-bottom))] duration-panel data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left",
        className,
      )}
      {...props}
    >
      {children}
      <Dialog.Close asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-2 top-2"
          aria-label="关闭导航"
        >
          <X aria-hidden="true" />
        </Button>
      </Dialog.Close>
    </Dialog.Content>
  </Dialog.Portal>
));
SheetContent.displayName = "SheetContent";

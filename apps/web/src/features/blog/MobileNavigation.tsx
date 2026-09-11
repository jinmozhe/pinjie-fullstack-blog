"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export function MobileNavigation({
  children,
  name,
}: {
  children: ReactNode;
  name: string;
}) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1024px)");
    const closeOnDesktop = () => {
      if (desktop.matches) setOpen(false);
    };
    desktop.addEventListener("change", closeOnDesktop);
    return () => desktop.removeEventListener("change", closeOnDesktop);
  }, []);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button type="button" variant="ghost" size="icon" aria-label="打开导航">
          <Menu aria-hidden="true" />
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetTitle className="mb-2 pr-10 text-card-title font-semibold [overflow-wrap:anywhere]">
          {name}
        </SheetTitle>
        <SheetDescription className="mb-8 text-meta text-muted-foreground">
          搜索文章，浏览分类与标签。
        </SheetDescription>
        {children}
      </SheetContent>
    </Sheet>
  );
}

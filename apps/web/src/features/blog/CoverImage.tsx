"use client";

import { useState } from "react";
import Image from "next/image";
import { ImageOff } from "lucide-react";

export function CoverImage({
  src,
  title,
  priority = false,
}: {
  src: string;
  title: string;
  priority?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="relative aspect-[2/1] overflow-hidden rounded-media bg-muted">
      {failed ? (
        <div
          role="img"
          aria-label={`${title}的封面加载失败`}
          className="flex h-full items-center justify-center gap-2 text-meta text-muted-foreground"
        >
          <ImageOff size={20} aria-hidden="true" />
          封面暂不可用
        </div>
      ) : (
        <Image
          src={src}
          alt=""
          fill
          unoptimized
          priority={priority}
          sizes="(max-width: 767px) 100vw, (max-width: 1279px) 50vw, 33vw"
          className="object-cover"
          onError={() => setFailed(true)}
        />
      )}
    </div>
  );
}

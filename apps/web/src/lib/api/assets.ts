"use client";

import type { AssetRead, UploadScene } from "@pinjie/api-client";

import { webRequest } from "./http";

export function uploadAsset(
  file: globalThis.File,
  scene: UploadScene = "attachment",
  signal?: globalThis.AbortSignal,
): Promise<AssetRead> {
  const body = new FormData();
  body.set("file", file);
  body.set("scene", scene);
  return webRequest<AssetRead>("/api/v1/assets/upload", { method: "POST", body }, true, signal);
}

export const assetApi = { upload: uploadAsset };

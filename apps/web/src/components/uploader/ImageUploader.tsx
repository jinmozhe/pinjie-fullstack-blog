"use client";

import type { AssetRead, UploadScene } from "@pinjie/api-client";
import { Upload } from "lucide-react";
import Image from "next/image";
import { useRef, useState } from "react";

import { assetApi } from "@/lib/api/assets";
import { errorMessage } from "@/lib/api/http";

export type ImageUploaderProps = {
  value?: string | null;
  onChange?: (url: string) => void;
  onUploaded?: (asset: AssetRead) => void;
  scene?: UploadScene;
  disabled?: boolean;
  maxSizeMb?: number;
  shape?: "image" | "avatar";
};

const IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export function ImageUploader({
  value,
  onChange,
  onUploaded,
  scene = "attachment",
  disabled = false,
  maxSizeMb = 5,
  shape = "image",
}: ImageUploaderProps) {
  const inputRef = useRef<globalThis.HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>();

  const upload = async (file?: globalThis.File) => {
    if (!file) return;
    if (!IMAGE_TYPES.has(file.type)) {
      setError("仅支持 JPG、PNG 或 WebP 图片");
      return;
    }
    if (file.size > maxSizeMb * 1024 * 1024) {
      setError(`图片大小不能超过 ${maxSizeMb} MB`);
      return;
    }
    setUploading(true);
    setError(undefined);
    try {
      const asset = await assetApi.upload(file, scene);
      onChange?.(asset.url);
      onUploaded?.(asset);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className={`image-uploader image-uploader--${shape}`}>
      {value && (
        <div className="image-uploader__preview">
          <Image src={value} alt="已上传图片" fill sizes={shape === "avatar" ? "88px" : "240px"} unoptimized />
        </div>
      )}
      <input
        ref={inputRef}
        aria-label="选择图片文件"
        accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
        disabled={disabled || uploading}
        hidden
        type="file"
        onChange={(event) => void upload(event.target.files?.[0])}
      />
      <button
        className="secondary-action"
        disabled={disabled || uploading}
        type="button"
        onClick={() => inputRef.current?.click()}
      >
        <Upload size={17} />
        {uploading ? "正在上传" : "选择图片"}
      </button>
      {error && <p className="form-alert" role="alert">{error}</p>}
    </div>
  );
}

export function AvatarUploader(props: Omit<ImageUploaderProps, "shape">) {
  return <ImageUploader {...props} scene={props.scene ?? "avatar"} maxSizeMb={props.maxSizeMb ?? 2} shape="avatar" />;
}

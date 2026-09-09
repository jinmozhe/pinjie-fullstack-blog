import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { assetApi } from "@/lib/api/assets";
import { AvatarUploader } from "./ImageUploader";

describe("AvatarUploader", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uploads an image through the shared Web request pipeline", async () => {
    const upload = vi.spyOn(assetApi, "upload").mockResolvedValue({
      id: "01900000-0000-7000-8000-000000000020",
      uploader_type: "user",
      uploader_id: "01900000-0000-7000-8000-000000000021",
      storage_driver: "local",
      file_key: "avatar/20260825/avatar.png",
      original_name: "avatar.png",
      mime_type: "image/png",
      file_size: 16,
      file_hash: "b".repeat(64),
      url: "/static/uploads/avatar/20260825/avatar.png",
      scene: "avatar",
      created_at: "2026-08-25T00:00:00Z",
      updated_at: "2026-08-25T00:00:00Z",
    });
    const onChange = vi.fn();
    const onUploaded = vi.fn();
    const user = userEvent.setup();
    render(<AvatarUploader onChange={onChange} onUploaded={onUploaded} />);

    await user.upload(
      screen.getByLabelText("选择图片文件"),
      new globalThis.File(["png-content"], "avatar.png", { type: "image/png" }),
    );

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith("/static/uploads/avatar/20260825/avatar.png");
    });
    expect(upload).toHaveBeenCalledWith(expect.any(globalThis.File), "avatar");
    expect(onUploaded).toHaveBeenCalledWith(expect.objectContaining({ id: "01900000-0000-7000-8000-000000000020" }));
  });

  it("rejects unsupported image types before sending a request", async () => {
    const onChange = vi.fn();
    render(<AvatarUploader onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("选择图片文件"), {
      target: { files: [new globalThis.File(["svg"], "avatar.svg", { type: "image/svg+xml" })] },
    });

    expect(await screen.findByRole("alert")).toHaveTextContent("仅支持 JPG、PNG 或 WebP 图片");
    expect(onChange).not.toHaveBeenCalled();
  });
});

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { StandardConfirmModal } from "./StandardConfirmModal";

describe("StandardConfirmModal", () => {
  it("does not execute on opening or cancellation", async () => {
    const onConfirm = vi.fn(async () => undefined);
    const onCancel = vi.fn();
    render(<StandardConfirmModal open loading={false} title="删除文件" description="删除后无法恢复" onCancel={onCancel} onConfirm={onConfirm} />);
    expect(onConfirm).not.toHaveBeenCalled();
    await userEvent.setup().click(screen.getByRole("button", { name: /取\s*消/ }));
    expect(onCancel).toHaveBeenCalledOnce();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("allows only one execution and prevents dismissal while the action is pending", async () => {
    let resolve: (() => void) | undefined;
    const pending = new Promise<void>((done) => { resolve = done; });
    const onConfirm = vi.fn(() => pending);
    const onCancel = vi.fn();
    render(<StandardConfirmModal open loading={false} title="删除文件" description="删除后无法恢复" onCancel={onCancel} onConfirm={onConfirm} />);
    const confirm = screen.getByRole("button", { name: /确\s*定/ });
    act(() => {
      fireEvent.click(confirm);
      fireEvent.click(confirm);
    });
    expect(onConfirm).toHaveBeenCalledOnce();
    expect(confirm).toBeDisabled();
    const cancel = screen.getByRole("button", { name: /取\s*消/ });
    expect(cancel).toBeDisabled();
    fireEvent.click(cancel);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape", keyCode: 27 });
    expect(onCancel).not.toHaveBeenCalled();
    await act(async () => { resolve?.(); await pending; });
    await waitFor(() => expect(confirm).toBeEnabled());
  });

  it("shows a failed action, retains the dialog and allows an explicit retry", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn<() => Promise<void>>()
      .mockRejectedValueOnce(new Error("文件仍被引用"))
      .mockResolvedValueOnce(undefined);
    render(<StandardConfirmModal open loading={false} title="删除文件" description="删除后无法恢复" onCancel={() => undefined} onConfirm={onConfirm} />);
    await user.click(screen.getByRole("button", { name: /确\s*定/ }));
    expect(await screen.findByText("文件仍被引用")).toBeVisible();
    expect(screen.getByRole("dialog")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /确\s*定/ }));
    await waitFor(() => expect(screen.queryByText("文件仍被引用")).not.toBeInTheDocument());
    expect(onConfirm).toHaveBeenCalledTimes(2);
  });
});

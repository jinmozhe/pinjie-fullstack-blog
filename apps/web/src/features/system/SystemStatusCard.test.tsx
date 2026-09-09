import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "@/test/setup";

import { SystemStatusCard } from "./SystemStatusCard";

describe("SystemStatusCard", () => {
  it("renders the server status and provides an accessible retry action", () => {
    render(<SystemStatusCard initialStatus={{ status: "available" }} />);
    expect(screen.getByRole("heading", { name: "系统运行状态" })).toBeInTheDocument();
    expect(screen.getByText("可用")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "重新检查" })).toBeInTheDocument();
  });

  it("refreshes the status when the user retries", async () => {
    render(<SystemStatusCard initialStatus={{ status: "unavailable" }} />);

    fireEvent.click(screen.getByRole("button", { name: "重新检查" }));

    await waitFor(() => expect(screen.getByText("可用")).toBeInTheDocument());
  });

  it("reports an unavailable backend when retry fails", async () => {
    server.use(
      http.get("http://127.0.0.1:3100/api/v1/system/status", () => HttpResponse.json({ message: "服务不可用" }, { status: 503 })),
    );
    render(<SystemStatusCard initialStatus={{ status: "available" }} />);

    fireEvent.click(screen.getByRole("button", { name: "重新检查" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("后端服务暂不可用"));
    expect(screen.getByText("不可用")).toBeInTheDocument();
  });
});

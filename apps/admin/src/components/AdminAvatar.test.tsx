import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AdminAvatar } from "./AdminAvatar";

describe("AdminAvatar", () => {
  it("renders uppercase English and Chinese fallback characters with theme colors", () => {
    const { rerender } = render(
      <AdminAvatar admin={{ avatar: null, display_name: "stage admin", username: "stage-admin" }} size={36} />,
    );
    const englishAvatar = screen.getByLabelText("stage admin的头像");
    expect(englishAvatar).toHaveTextContent("S");
    expect(englishAvatar).toHaveStyle({ color: "rgba(0, 0, 0, 0.65)" });

    rerender(<AdminAvatar admin={{ avatar: null, display_name: "管理员", username: "stage-admin" }} size={36} />);
    expect(screen.getByLabelText("管理员的头像")).toHaveTextContent("管");
  });

  it("shows the fallback character when the configured image fails to load", () => {
    render(
      <AdminAvatar
        admin={{ avatar: "/static/uploads/avatar/missing.png", display_name: "管理员", username: "stage-admin" }}
        size={36}
      />,
    );

    fireEvent.error(screen.getByRole("img", { name: "管理员的头像" }));
    expect(screen.getByLabelText("管理员的头像")).toHaveTextContent("管");
  });

  it("uses the user icon when no fallback character is available", () => {
    const { container } = render(
      <AdminAvatar admin={{ avatar: null, display_name: null, username: "" }} size={36} />,
    );
    expect(container.querySelector(".anticon-user")).not.toBeNull();
  });
});

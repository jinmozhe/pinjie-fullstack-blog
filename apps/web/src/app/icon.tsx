import { ImageResponse } from "next/og";

export const alt = "Pinjie";
export const contentType = "image/png";
export const size = { width: 64, height: 64 };

export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        alignItems: "center",
        background: "#17181b",
        border: "4px solid #e5484d",
        color: "#ffffff",
        display: "flex",
        fontSize: 40,
        fontWeight: 800,
        height: "100%",
        justifyContent: "center",
        width: "100%",
      }}
    >
      P
    </div>,
    size,
  );
}

import type { AdminRead } from "@pinjie/api-client";
import { UserOutlined } from "@ant-design/icons";
import { Avatar, theme } from "antd";
import type { AvatarProps } from "antd";

type AdminAvatarIdentity = Pick<AdminRead, "avatar" | "display_name" | "username">;

type AdminAvatarProps = {
  admin: AdminAvatarIdentity;
  size?: AvatarProps["size"];
};

function fallbackAvatarText(admin: AdminAvatarIdentity): string {
  const name = admin.display_name?.trim() || admin.username.trim();
  return (Array.from(name)[0] ?? "").toUpperCase();
}

export function AdminAvatar({ admin, size = "small" }: AdminAvatarProps) {
  const { token } = theme.useToken();
  const name = admin.display_name?.trim() || admin.username.trim();
  const fallback = fallbackAvatarText(admin);

  return (
    <Avatar
      size={size}
      src={admin.avatar?.trim() || undefined}
      alt={`${name}的头像`}
      aria-label={`${name}的头像`}
      icon={fallback ? undefined : <UserOutlined />}
      style={{ backgroundColor: token.colorFillSecondary, color: token.colorTextSecondary }}
    >
      {fallback || undefined}
    </Avatar>
  );
}

export default AdminAvatar;

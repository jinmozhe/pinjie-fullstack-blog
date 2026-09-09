import { UserOutlined } from "@ant-design/icons";
import { Avatar, Flex } from "antd";

import { ImageUploader, type ImageUploaderProps } from "./ImageUploader";

export function AvatarUploader(props: ImageUploaderProps) {
  return (
    <Flex align="center" gap={16} wrap="wrap">
      <Avatar
        size={88}
        src={props.value || undefined}
        alt="头像预览"
        icon={<UserOutlined />}
        style={{ border: "1px solid #e5e7eb", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
      />
      <ImageUploader {...props} />
    </Flex>
  );
}

export default AvatarUploader;

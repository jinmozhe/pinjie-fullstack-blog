import { Button, Tag, Tooltip } from "antd";

type StatusToggleTagProps = {
  active: boolean;
  ariaLabel: string;
  interactive: boolean;
  loading?: boolean;
  readOnlyReason?: string;
  onToggle: () => void;
};

export function StatusToggleTag({
  active,
  ariaLabel,
  interactive,
  loading = false,
  readOnlyReason,
  onToggle,
}: StatusToggleTagProps) {
  const tag = <Tag color={active ? "success" : "default"}>{active ? "正常" : "停用"}</Tag>;

  if (!interactive) {
    return (
      <Tooltip title={readOnlyReason}>
        <span>{tag}</span>
      </Tooltip>
    );
  }

  return (
    <Tooltip title={active ? "停用" : "启用"}>
      <Button
        aria-label={ariaLabel}
        aria-pressed={active}
        className="status-tag-button"
        loading={loading}
        size="small"
        type="text"
        onClick={onToggle}
      >
        {tag}
      </Button>
    </Tooltip>
  );
}

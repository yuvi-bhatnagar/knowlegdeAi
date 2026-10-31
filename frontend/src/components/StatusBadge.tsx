import React from "react";

export type StatusVariant =
  | "uploaded"
  | "processing"
  | "completed"
  | "failed"
  | "admin"
  | "user"
  | "active"
  | "inactive"
  | "ready"
  | "healthy"
  | "degraded"
  | string;

export interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
  showDot?: boolean;
  size?: "sm" | "md";
  style?: React.CSSProperties;
}

const statusColorMap: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  uploaded: {
    bg: "rgba(59, 130, 246, 0.15)",
    text: "#60a5fa",
    border: "rgba(59, 130, 246, 0.3)",
    dot: "#3b82f6",
  },
  processing: {
    bg: "rgba(245, 158, 11, 0.15)",
    text: "#fbbf24",
    border: "rgba(245, 158, 11, 0.3)",
    dot: "#f59e0b",
  },
  completed: {
    bg: "rgba(16, 185, 129, 0.15)",
    text: "#34d399",
    border: "rgba(16, 185, 129, 0.3)",
    dot: "#10b981",
  },
  ready: {
    bg: "rgba(16, 185, 129, 0.15)",
    text: "#34d399",
    border: "rgba(16, 185, 129, 0.3)",
    dot: "#10b981",
  },
  healthy: {
    bg: "rgba(16, 185, 129, 0.15)",
    text: "#34d399",
    border: "rgba(16, 185, 129, 0.3)",
    dot: "#10b981",
  },
  failed: {
    bg: "rgba(239, 68, 68, 0.15)",
    text: "#f87171",
    border: "rgba(239, 68, 68, 0.3)",
    dot: "#ef4444",
  },
  admin: {
    bg: "rgba(239, 68, 68, 0.15)",
    text: "#f87171",
    border: "rgba(239, 68, 68, 0.3)",
    dot: "#ef4444",
  },
  user: {
    bg: "rgba(148, 163, 184, 0.15)",
    text: "#94a3b8",
    border: "rgba(148, 163, 184, 0.3)",
    dot: "#94a3b8",
  },
  active: {
    bg: "rgba(16, 185, 129, 0.15)",
    text: "#34d399",
    border: "rgba(16, 185, 129, 0.3)",
    dot: "#10b981",
  },
  inactive: {
    bg: "rgba(100, 116, 139, 0.15)",
    text: "#94a3b8",
    border: "rgba(100, 116, 139, 0.3)",
    dot: "#64748b",
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  showDot = true,
  size = "md",
  style,
}) => {
  const normKey = (status || "").toLowerCase();
  const theme = statusColorMap[normKey] || {
    bg: "rgba(100, 116, 139, 0.15)",
    text: "#cbd5e1",
    border: "rgba(100, 116, 139, 0.3)",
    dot: "#94a3b8",
  };

  const isSmall = size === "sm";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: isSmall ? "4px" : "6px",
        padding: isSmall ? "2px 7px" : "3px 9px",
        fontSize: isSmall ? "11px" : "12px",
        fontWeight: "600",
        borderRadius: "9999px",
        textTransform: "capitalize",
        backgroundColor: theme.bg,
        color: theme.text,
        border: `1px solid ${theme.border}`,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {showDot && (
        <span
          style={{
            width: isSmall ? "5px" : "6px",
            height: isSmall ? "5px" : "6px",
            borderRadius: "50%",
            backgroundColor: theme.dot,
            display: "inline-block",
            flexShrink: 0,
          }}
        />
      )}
      {label || status}
    </span>
  );
};


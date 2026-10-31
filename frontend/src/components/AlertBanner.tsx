import React from "react";
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

export type AlertVariant = "error" | "success" | "warning" | "info";

export interface AlertBannerProps {
  variant?: AlertVariant;
  message: string;
  onClose?: () => void;
  style?: React.CSSProperties;
  className?: string;
}

const variantStyles: Record<AlertVariant, { bg: string; border: string; color: string; icon: React.ReactNode }> = {
  error: {
    bg: "rgba(239, 68, 68, 0.12)",
    border: "rgba(239, 68, 68, 0.3)",
    color: "#f87171",
    icon: <AlertCircle size={18} style={{ flexShrink: 0 }} />,
  },
  success: {
    bg: "rgba(16, 185, 129, 0.12)",
    border: "rgba(16, 185, 129, 0.3)",
    color: "#34d399",
    icon: <CheckCircle2 size={18} style={{ flexShrink: 0 }} />,
  },
  warning: {
    bg: "rgba(245, 158, 11, 0.12)",
    border: "rgba(245, 158, 11, 0.3)",
    color: "#fbbf24",
    icon: <AlertTriangle size={18} style={{ flexShrink: 0 }} />,
  },
  info: {
    bg: "rgba(59, 130, 246, 0.12)",
    border: "rgba(59, 130, 246, 0.3)",
    color: "#60a5fa",
    icon: <Info size={18} style={{ flexShrink: 0 }} />,
  },
};

export const AlertBanner: React.FC<AlertBannerProps> = ({
  variant = "error",
  message,
  onClose,
  style,
  className,
}) => {
  const conf = variantStyles[variant];

  return (
    <div
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
        padding: "12px 16px",
        borderRadius: "8px",
        backgroundColor: conf.bg,
        border: `1px solid ${conf.border}`,
        color: conf.color,
        fontSize: "13.5px",
        lineHeight: "1.5",
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
        ...style,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, minWidth: 0 }}>
        {conf.icon}
        <span style={{ wordBreak: "break-word" }}>{message}</span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          aria-label="Dismiss alert"
          style={{
            background: "none",
            border: "none",
            color: conf.color,
            cursor: "pointer",
            padding: "4px",
            borderRadius: "4px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            opacity: 0.85,
            transition: "opacity 0.15s ease",
            flexShrink: 0,
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.85")}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};


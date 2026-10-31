import React from "react";

export interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: React.ReactNode;
  iconBg?: string;
  iconBorder?: string;
  iconColor?: string;
  badge?: React.ReactNode;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  iconBg = "rgba(59, 130, 246, 0.15)",
  iconBorder = "rgba(59, 130, 246, 0.3)",
  badge,
  onClick,
  style,
}) => {
  return (
    <div
      className="glass-card"
      onClick={onClick}
      style={{
        padding: "20px 24px",
        cursor: onClick ? "pointer" : "default",
        transition: "all 0.2s ease",
        ...style,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--text-secondary)", fontSize: "13px", fontWeight: "500", marginBottom: "6px" }}>
            {title}
          </div>
          <div style={{ fontSize: "28px", fontWeight: "700", letterSpacing: "-0.5px" }}>
            {value}
          </div>
          {subtext && (
            <div style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "4px" }}>
              {subtext}
            </div>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              backgroundColor: iconBg,
              border: `1px solid ${iconBorder}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          {badge}
        </div>
      </div>
    </div>
  );
};


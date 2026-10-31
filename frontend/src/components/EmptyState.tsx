import React from "react";

export interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  style?: React.CSSProperties;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  style,
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "48px 24px",
        margin: "auto",
        maxWidth: "440px",
        ...style,
      }}
    >
      <div
        style={{
          width: "52px",
          height: "52px",
          borderRadius: "14px",
          backgroundColor: "rgba(59, 130, 246, 0.12)",
          border: "1px solid rgba(59, 130, 246, 0.25)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "16px",
          color: "var(--accent-blue)",
        }}
      >
        {icon}
      </div>
      <h3
        style={{
          fontSize: "16px",
          fontWeight: "600",
          color: "var(--text-primary)",
          marginBottom: "8px",
        }}
      >
        {title}
      </h3>
      <p
        style={{
          fontSize: "13.5px",
          color: "var(--text-secondary)",
          lineHeight: "1.55",
          marginBottom: action ? "20px" : "0",
        }}
      >
        {description}
      </p>
      {action && (
        <button
          type="button"
          className="btn btn-primary"
          onClick={action.onClick}
          style={{ fontSize: "13px", padding: "8px 16px" }}
        >
          {action.icon}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
};


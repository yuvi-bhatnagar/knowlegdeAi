import React from "react";

export interface LoadingStateProps {
  label?: string;
  size?: "sm" | "md" | "lg";
  fullPage?: boolean;
  style?: React.CSSProperties;
}

const spinnerSizes = {
  sm: { width: "16px", height: "16px", borderWidth: "2px" },
  md: { width: "24px", height: "24px", borderWidth: "2.5px" },
  lg: { width: "36px", height: "36px", borderWidth: "3px" },
};

export const LoadingState: React.FC<LoadingStateProps> = ({
  label = "Loading...",
  size = "md",
  fullPage = false,
  style,
}) => {
  const sizeStyles = spinnerSizes[size];

  const content = (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "12px",
        color: "var(--text-secondary)",
        fontSize: "13.5px",
        ...style,
      }}
    >
      <div
        className="spinner"
        style={{
          ...sizeStyles,
          margin: 0,
        }}
      />
      {label && <span>{label}</span>}
    </div>
  );

  if (fullPage) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "50vh",
          width: "100%",
        }}
      >
        {content}
      </div>
    );
  }

  return content;
};


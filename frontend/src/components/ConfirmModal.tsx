import React, { useEffect } from "react";
import { Trash2, AlertTriangle, X } from "lucide-react";

export interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "primary" | "warning";
  icon?: "trash" | "warning";
  isLoading?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmText = "Delete",
  cancelText = "Cancel",
  variant = "danger",
  icon = "trash",
  isLoading = false,
  onConfirm,
  onCancel,
}) => {
  // Listen for Escape key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isLoading) {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isLoading, onCancel]);

  if (!isOpen) return null;

  const isDanger = variant === "danger";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(10, 15, 29, 0.75)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        zIndex: 9999,
      }}
      onClick={() => {
        if (!isLoading) onCancel();
      }}
    >
      <div
        className="glass-card"
        style={{
          maxWidth: "460px",
          width: "100%",
          padding: "24px 26px",
          position: "relative",
          backgroundColor: "#1e293b",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05)",
          borderRadius: "14px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onCancel}
          disabled={isLoading}
          aria-label="Close dialog"
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            cursor: isLoading ? "not-allowed" : "pointer",
            padding: "4px",
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "color 0.15s ease",
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-primary)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "var(--text-muted)")}
        >
          <X size={18} />
        </button>

        {/* Modal Header & Content */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "16px" }}>
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              backgroundColor: isDanger ? "rgba(239, 68, 68, 0.15)" : "rgba(59, 130, 246, 0.15)",
              border: `1px solid ${isDanger ? "rgba(239, 68, 68, 0.3)" : "rgba(59, 130, 246, 0.3)"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {icon === "trash" ? (
              <Trash2 size={20} color={isDanger ? "#f87171" : "#60a5fa"} />
            ) : (
              <AlertTriangle size={20} color={isDanger ? "#f87171" : "#fbbf24"} />
            )}
          </div>

          <div style={{ flex: 1, paddingRight: "14px" }}>
            <h3
              style={{
                fontSize: "17px",
                fontWeight: "600",
                color: "var(--text-primary)",
                marginBottom: "6px",
              }}
            >
              {title}
            </h3>
            <p
              style={{
                fontSize: "13.5px",
                color: "var(--text-secondary)",
                lineHeight: "1.55",
                margin: 0,
                wordBreak: "break-word",
              }}
            >
              {message}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: "10px",
            marginTop: "22px",
            paddingTop: "16px",
            borderTop: "1px solid rgba(51, 65, 85, 0.6)",
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: "500",
            }}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={isDanger ? "btn btn-danger" : "btn btn-primary"}
            onClick={onConfirm}
            disabled={isLoading}
            style={{
              padding: "8px 18px",
              fontSize: "13px",
              fontWeight: "600",
              backgroundColor: isDanger ? "#ef4444" : undefined,
              color: isDanger ? "#ffffff" : undefined,
              border: isDanger ? "1px solid #dc2626" : undefined,
            }}
          >
            {isLoading ? (
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span className="spinner" style={{ width: "13px", height: "13px" }} />
                <span>Processing...</span>
              </div>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
};


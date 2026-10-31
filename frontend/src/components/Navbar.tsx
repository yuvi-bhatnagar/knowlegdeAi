import React from "react";
import { useAuth } from "../context/AuthContext";
import {
  BookOpen,
  MessageSquare,
  Files,
  LogOut,
  User as UserIcon,
  ShieldCheck,
} from "lucide-react";

interface NavbarProps {
  activeTab: "dashboard" | "documents" | "chat" | "admin";
  setActiveTab: (tab: "dashboard" | "documents" | "chat" | "admin") => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const { user, logout } = useAuth();
  const isAdmin = Boolean(user?.is_superuser || user?.role === "admin");

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border-color)",
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
        padding: "0 24px",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Brand */}
      <div
        style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}
        onClick={() => setActiveTab("dashboard")}
      >
        <div
          style={{
            background: "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
            padding: "8px",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <BookOpen size={22} color="#ffffff" />
        </div>
        <div>
          <span style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "-0.5px" }}>KnowledgeAI</span>
          <span
            style={{
              fontSize: "10px",
              backgroundColor: "rgba(59, 130, 246, 0.2)",
              color: "#60a5fa",
              padding: "2px 6px",
              borderRadius: "4px",
              marginLeft: "8px",
              fontWeight: "600",
            }}
          >
            RAG ASSISTANT
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ display: "flex", gap: "8px" }}>
        <button
          className={`btn ${activeTab === "dashboard" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveTab("dashboard")}
          style={{ padding: "8px 14px", fontSize: "13px" }}
        >
          Overview
        </button>
        <button
          className={`btn ${activeTab === "documents" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveTab("documents")}
          style={{ padding: "8px 14px", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}
        >
          <Files size={16} />
          <span>Documents</span>
        </button>
        <button
          className={`btn ${activeTab === "chat" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveTab("chat")}
          style={{ padding: "8px 14px", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}
        >
          <MessageSquare size={16} />
          <span>Chat</span>
        </button>

        {/* Admin Tab - strictly visible only for admins */}
        {isAdmin && (
          <button
            className={`btn ${activeTab === "admin" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("admin")}
            style={{
              padding: "8px 14px",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              backgroundColor: activeTab === "admin" ? undefined : "rgba(239, 68, 68, 0.1)",
              borderColor: activeTab === "admin" ? undefined : "rgba(239, 68, 68, 0.35)",
              color: activeTab === "admin" ? undefined : "#f87171",
            }}
          >
            <ShieldCheck size={16} />
            <span>Admin Console</span>
          </button>
        )}
      </nav>

      {/* User Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "var(--text-secondary)" }}>
          <UserIcon size={16} />
          <span>{user?.email}</span>
          {isAdmin && (
            <span
              style={{
                fontSize: "10px",
                fontWeight: "700",
                backgroundColor: "rgba(239, 68, 68, 0.2)",
                color: "#f87171",
                padding: "2px 6px",
                borderRadius: "4px",
                border: "1px solid rgba(239, 68, 68, 0.3)",
              }}
            >
              ADMIN
            </span>
          )}
        </div>
        <button
          className="btn btn-secondary"
          onClick={logout}
          title="Sign Out"
          style={{ padding: "8px 12px", fontSize: "13px" }}
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
};

import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { StatCard } from "../components";
import {
  Files,
  MessageSquare,
  Sparkles,
  Upload,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  FileText,
  Search,
} from "lucide-react";

interface DashboardPageProps {
  onNavigate: (tab: "documents" | "chat") => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [docCount, setDocCount] = useState<number>(0);
  const [chunkCount, setChunkCount] = useState<number>(0);
  const [convCount, setConvCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUserStats() {
      try {
        const [docsRes, convsRes] = await Promise.allSettled([
          api.listDocuments(1, 100),
          api.listConversations(1, 100),
        ]);

        if (docsRes.status === "fulfilled") {
          setDocCount(docsRes.value.total);
          const totalChunks = docsRes.value.items.reduce(
            (acc, d) => acc + (d.chunk_count || 0),
            0
          );
          setChunkCount(totalChunks);
        }

        if (convsRes.status === "fulfilled") {
          setConvCount(convsRes.value.total);
        }
      } finally {
        setLoading(false);
      }
    }

    loadUserStats();
  }, []);

  const userName = user?.email.split("@")[0] || "User";

  return (
    <div style={{ padding: "32px 24px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
      {/* User Welcome Banner */}
      <div
        className="glass-card"
        style={{
          padding: "36px",
          marginBottom: "32px",
          background: "linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{ maxWidth: "640px", position: "relative", zIndex: 1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              color: "var(--accent-blue)",
              marginBottom: "10px",
            }}
          >
            <Sparkles size={18} />
            <span style={{ fontSize: "12px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "1px" }}>
              Personal Knowledge Workspace
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", marginBottom: "12px" }}>
            Welcome back, {userName}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "15px", lineHeight: "1.6", marginBottom: "24px" }}>
            Your personal AI assistant is grounded strictly in your uploaded documents. Ask questions, receive verified source citations, and explore your knowledge base.
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => onNavigate("documents")}>
              <Upload size={16} />
              <span>Upload Document</span>
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate("chat")}>
              <MessageSquare size={16} />
              <span>Open Chat Assistant</span>
            </button>
          </div>
        </div>
      </div>

      {/* User Personal Metrics Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "20px",
          marginBottom: "32px",
        }}
      >
        <StatCard
          title="My Ingested Documents"
          value={loading ? "..." : docCount}
          subtext="PDF, TXT, & Markdown files"
          icon={<Files size={24} color="#60a5fa" />}
          iconBg="rgba(59, 130, 246, 0.15)"
          iconBorder="rgba(59, 130, 246, 0.3)"
          onClick={() => onNavigate("documents")}
        />

        <StatCard
          title="Searchable Chunks"
          value={loading ? "..." : chunkCount}
          subtext="Indexed with page metadata"
          icon={<Search size={24} color="#34d399" />}
          iconBg="rgba(16, 185, 129, 0.15)"
          iconBorder="rgba(16, 185, 129, 0.3)"
        />

        <StatCard
          title="Active Conversations"
          value={loading ? "..." : convCount}
          subtext="Persistent question history"
          icon={<MessageSquare size={24} color="#fbbf24" />}
          iconBg="rgba(245, 158, 11, 0.15)"
          iconBorder="rgba(245, 158, 11, 0.3)"
          onClick={() => onNavigate("chat")}
        />

        <StatCard
          title="Answer Verification"
          value="Verified Citations"
          subtext="Anti-hallucination validation"
          icon={<ShieldCheck size={24} color="#a78bfa" />}
          iconBg="rgba(139, 92, 246, 0.15)"
          iconBorder="rgba(139, 92, 246, 0.3)"
        />
      </div>

      {/* How it Works / Workflow Guide */}
      <div className="glass-card" style={{ padding: "32px" }}>
        <h3 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px" }}>
          How to Use Your Knowledge Assistant
        </h3>
        <p style={{ fontSize: "14px", color: "var(--text-secondary)", marginBottom: "24px" }}>
          KnowledgeAI ensures answers are strictly grounded in your documents with real page numbers and excerpts.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px" }}>
          {/* Step 1 */}
          <div
            style={{
              padding: "20px",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              borderRadius: "10px",
              border: "1px solid var(--border-color)",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "rgba(59, 130, 246, 0.2)",
                color: "#60a5fa",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "700",
                marginBottom: "12px",
              }}
            >
              1
            </div>
            <h4 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "6px" }}>Upload Your Files</h4>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              Upload PDF manuals, notes, Markdown docs, or text files. PyMuPDF extracts text preserving accurate page boundaries.
            </p>
          </div>

          {/* Step 2 */}
          <div
            style={{
              padding: "20px",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              borderRadius: "10px",
              border: "1px solid var(--border-color)",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "rgba(16, 185, 129, 0.2)",
                color: "#34d399",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "700",
                marginBottom: "12px",
              }}
            >
              2
            </div>
            <h4 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "6px" }}>Automatic Vector Indexing</h4>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              Background workers split your content into chunks with contextual overlap and index vectors in Qdrant with tenant isolation.
            </p>
          </div>

          {/* Step 3 */}
          <div
            style={{
              padding: "20px",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              borderRadius: "10px",
              border: "1px solid var(--border-color)",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "rgba(139, 92, 246, 0.2)",
                color: "#a78bfa",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "700",
                marginBottom: "12px",
              }}
            >
              3
            </div>
            <h4 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "6px" }}>Ask &amp; Verify Citations</h4>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              Ask any question. The assistant retrieves relevant evidence and responds with verified clickable citations referencing real document pages.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

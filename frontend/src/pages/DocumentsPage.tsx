import React, { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { DocumentItem } from "../types";
import {
  ConfirmModal,
  AlertBanner,
  SearchInput,
  StatusBadge,
  LoadingState,
  EmptyState,
} from "../components";
import {
  Upload,
  FileText,
  Trash2,
  RotateCw,
  Clock,
  FileCode,
  File,
} from "lucide-react";

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [docToDelete, setDocToDelete] = useState<DocumentItem | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const res = await api.listDocuments(1, 100);
      setDocuments(res.items);
    } catch (err: any) {
      setError(err.message || "Failed to load documents.");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(true);
  }, []);

  // Poll while any document is in uploaded or processing state
  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === "uploaded" || d.status === "processing"
    );
    if (!hasPending) return;

    const interval = setInterval(() => {
      fetchDocuments(false);
    }, 3500);

    return () => clearInterval(interval);
  }, [documents]);

  const handleFileUpload = async (file: File) => {
    setError(null);
    setSuccessMsg(null);
    setUploading(true);

    try {
      const res = await api.uploadDocument(file);
      setSuccessMsg(`"${file.name}" uploaded successfully and queued for indexing!`);
      await fetchDocuments(false);
    } catch (err: any) {
      setError(err.message || "Upload failed. Please verify file format and size.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleConfirmDelete = async () => {
    if (!docToDelete) return;
    setDeleting(true);
    setError(null);

    try {
      await api.deleteDocument(docToDelete.id);
      setDocuments((prev) => prev.filter((d) => d.id !== docToDelete.id));
      setSuccessMsg(`Document "${docToDelete.original_filename}" deleted successfully.`);
      setDocToDelete(null);
    } catch (err: any) {
      setError(err.message || "Failed to delete document.");
    } finally {
      setDeleting(false);
    }
  };

  const handleRetry = async (doc: DocumentItem) => {
    try {
      await api.retryDocument(doc.id);
      await fetchDocuments(false);
      setSuccessMsg(`Indexing retry queued for "${doc.original_filename}".`);
    } catch (err: any) {
      setError(err.message || "Retry failed.");
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDisplayError = (msg?: string | null): string => {
    if (!msg) return "";
    const lower = msg.toLowerCase();
    if (
      msg.includes("429") ||
      lower.includes("resource_exhausted") ||
      lower.includes("quota") ||
      lower.includes("rate limit")
    ) {
      return "Embedding quota limit temporarily reached on Free Tier. Click 'Retry' in 1 minute to resume indexing.";
    }
    if (msg.includes("404") || lower.includes("not found")) {
      return "Configured embedding model unavailable. Please check settings in Admin Console.";
    }
    if (
      msg.includes("401") ||
      msg.includes("403") ||
      lower.includes("api key") ||
      lower.includes("unauthorized") ||
      lower.includes("permission_denied")
    ) {
      return "Provider authentication failed. Please verify API credentials in Admin Console.";
    }
    if (msg.includes("{") && msg.includes("}")) {
      return "Document indexing paused due to a provider limit. Click 'Retry' to resume.";
    }
    return msg;
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "pdf") return <FileText size={18} color="#f87171" />;
    if (ext === "md" || ext === "markdown") return <FileCode size={18} color="#60a5fa" />;
    return <File size={18} color="#94a3b8" />;
  };

  const filteredDocs = documents.filter((d) =>
    d.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ padding: "32px 24px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
      {/* Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: "700", marginBottom: "4px" }}>Document Library</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
            Upload, inspect, and manage documents indexed for your grounded AI assistant.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <AlertBanner
          variant="error"
          message={error}
          onClose={() => setError(null)}
          style={{ marginBottom: "20px" }}
        />
      )}

      {successMsg && (
        <AlertBanner
          variant="success"
          message={successMsg}
          onClose={() => setSuccessMsg(null)}
          style={{ marginBottom: "20px" }}
        />
      )}

      {/* Upload Dropzone */}
      <div
        className="glass-card"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{
          padding: "36px",
          textAlign: "center",
          border: "2px dashed var(--border-color)",
          marginBottom: "32px",
          cursor: "pointer",
          backgroundColor: uploading ? "rgba(30, 41, 59, 0.95)" : "rgba(30, 41, 59, 0.5)",
          transition: "all 0.2s ease",
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept=".pdf,.txt,.md,.markdown"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          backgroundColor: "rgba(59, 130, 246, 0.15)",
          color: "var(--accent-blue)",
          marginBottom: "14px",
        }}>
          {uploading ? <div className="spinner" /> : <Upload size={26} />}
        </div>
        <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "6px" }}>
          {uploading ? "Uploading & Extracting..." : "Click or drag & drop documents here"}
        </h3>
        <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
          Supports <strong>PDF</strong>, <strong>TXT</strong>, and <strong>Markdown</strong> files up to 25 MB.
        </p>
      </div>

      {/* Search Bar & Refresh */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", alignItems: "center" }}>
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search documents by filename..."
          style={{ flex: 1, maxWidth: "none" }}
        />
        <button
          className="btn btn-secondary"
          onClick={() => fetchDocuments(true)}
          title="Refresh list"
        >
          <RotateCw size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Documents Table */}
      <div className="glass-card" style={{ overflow: "hidden" }}>
        {loading ? (
          <LoadingState label="Loading document library..." style={{ padding: "48px" }} />
        ) : filteredDocs.length === 0 ? (
          <EmptyState
            icon={<FileText size={26} />}
            title="No documents found"
            description={
              searchQuery
                ? "No uploaded documents match your search query."
                : "Upload your first PDF or Markdown document above to begin grounding your assistant."
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-secondary)" }}>
                  <th style={{ padding: "14px 20px" }}>Document</th>
                  <th style={{ padding: "14px 20px" }}>Size</th>
                  <th style={{ padding: "14px 20px" }}>Status</th>
                  <th style={{ padding: "14px 20px" }}>Chunks</th>
                  <th style={{ padding: "14px 20px" }}>Date</th>
                  <th style={{ padding: "14px 20px", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: "1px solid rgba(51, 65, 85, 0.5)" }}>
                    <td style={{ padding: "14px 20px", display: "flex", alignItems: "center", gap: "10px", fontWeight: "500" }}>
                      {getFileIcon(doc.original_filename)}
                      <div>
                        <div>{doc.original_filename}</div>
                        {doc.error_summary && (
                          <div style={{ fontSize: "11px", color: "#f87171", marginTop: "2px" }}>
                            {formatDisplayError(doc.error_summary)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: "14px 20px", color: "var(--text-secondary)" }}>
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td style={{ padding: "14px 20px" }}>
                      <StatusBadge status={doc.status} />
                    </td>
                    <td style={{ padding: "14px 20px", color: "var(--text-secondary)" }}>
                      {doc.chunk_count}
                    </td>
                    <td style={{ padding: "14px 20px", color: "var(--text-muted)" }}>
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "14px 20px", textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "8px" }}>
                        {doc.status === "failed" && (
                          <button
                            className="btn btn-secondary"
                            onClick={() => handleRetry(doc)}
                            title="Retry indexing"
                            style={{ padding: "6px 10px", fontSize: "12px" }}
                          >
                            <RotateCw size={14} />
                            <span>Retry</span>
                          </button>
                        )}
                        <button
                          className="btn btn-danger"
                          onClick={() => setDocToDelete(doc)}
                          title="Delete document"
                          style={{ padding: "6px 10px" }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Custom Confirmation Modal */}
      <ConfirmModal
        isOpen={!!docToDelete}
        title="Delete Document"
        message={`Are you sure you want to delete "${docToDelete?.original_filename}"? This will permanently remove the file and all associated vector embeddings and chunks.`}
        confirmText="Delete Document"
        cancelText="Cancel"
        variant="danger"
        icon="trash"
        isLoading={deleting}
        onCancel={() => {
          if (!deleting) setDocToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
};


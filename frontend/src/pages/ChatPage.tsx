import React, { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { Citation, ConversationItem, DocumentItem, MessageItem } from "../types";
import { ConfirmModal, Modal, AlertBanner, EmptyState, LoadingState } from "../components";
import {
  MessageSquare,
  Plus,
  Send,
  Trash2,
  Edit2,
  Check,
  X,
  FileText,
  Sparkles,
  Info,
  Filter,
  ExternalLink,
} from "lucide-react";

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [loadingConv, setLoadingConv] = useState<boolean>(true);
  const [loadingMessages, setLoadingMessages] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState<string>("");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [convToDelete, setConvToDelete] = useState<ConversationItem | null>(null);
  const [deletingConv, setDeletingConv] = useState<boolean>(false);
  const [chatError, setChatError] = useState<string | null>(null);

  // Available documents for optional filtering
  const [allDocs, setAllDocs] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [showFilterDropdown, setShowFilterDropdown] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    loadConversations();
    loadDocuments();
  }, []);

  useEffect(() => {
    if (activeConvId) {
      loadMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const loadDocuments = async () => {
    try {
      const res = await api.listDocuments(1, 100);
      setAllDocs(res.items.filter((d) => d.status === "completed"));
    } catch {
      // Non-blocking
    }
  };

  const loadConversations = async () => {
    setLoadingConv(true);
    try {
      const res = await api.listConversations(1, 50);
      setConversations(res.items);
      if (res.items.length > 0 && !activeConvId) {
        setActiveConvId(res.items[0].id);
      }
    } finally {
      setLoadingConv(false);
    }
  };

  const loadMessages = async (convId: string) => {
    setLoadingMessages(true);
    try {
      const msgs = await api.getMessages(convId);
      setMessages(msgs);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleCreateNewThread = async () => {
    try {
      setChatError(null);
      const newConv = await api.createConversation("New Conversation");
      setConversations([newConv, ...conversations]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err: any) {
      setChatError(err.message || "Failed to create conversation.");
    }
  };

  const handleOpenDeleteModal = (conv: ConversationItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setConvToDelete(conv);
  };

  const handleConfirmDeleteConv = async () => {
    if (!convToDelete) return;
    setDeletingConv(true);
    setChatError(null);

    try {
      await api.deleteConversation(convToDelete.id);
      const remaining = conversations.filter((c) => c.id !== convToDelete.id);
      setConversations(remaining);
      if (activeConvId === convToDelete.id) {
        setActiveConvId(remaining.length > 0 ? remaining[0].id : null);
      }
      setConvToDelete(null);
    } catch (err: any) {
      setChatError(err.message || "Failed to delete conversation.");
    } finally {
      setDeletingConv(false);
    }
  };

  const handleSaveTitle = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!newTitle.trim()) {
      setEditingTitleId(null);
      return;
    }
    try {
      setChatError(null);
      const updated = await api.updateConversation(convId, newTitle.trim());
      setConversations(conversations.map((c) => (c.id === convId ? updated : c)));
      setEditingTitleId(null);
    } catch (err: any) {
      setChatError(err.message || "Failed to rename conversation.");
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || sending) return;

    setInputQuery("");
    setSending(true);

    // Optimistically add user turn to local UI
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      conversation_id: activeConvId || "new",
      role: "user",
      content: query,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const chatRes = await api.chat(
        query,
        activeConvId,
        selectedDocIds.length > 0 ? selectedDocIds : null
      );

      // If active conversation was null, set the new conversation id
      if (!activeConvId) {
        setActiveConvId(chatRes.conversation_id);
        await loadConversations();
      }

      // Add assistant message
      const assistantMsg: MessageItem = {
        id: chatRes.message_id,
        conversation_id: chatRes.conversation_id,
        role: "assistant",
        content: chatRes.answer,
        sources: chatRes.citations || [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: MessageItem = {
        id: "err-" + Date.now(),
        conversation_id: activeConvId || "unknown",
        role: "assistant",
        content: `Error: ${err.message || "Failed to generate answer."}`,
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  };

  const activeConv = conversations.find((c) => c.id === activeConvId);

  return (
    <div style={{ display: "flex", height: "calc(100vh - 64px)", width: "100%", overflow: "hidden" }}>
      {/* Sidebar Threads */}
      <div style={{
        width: "280px",
        borderRight: "1px solid var(--border-color)",
        backgroundColor: "rgba(15, 23, 42, 0.7)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
      }}>
        <div style={{ padding: "16px", borderBottom: "1px solid var(--border-color)" }}>
          <button
            className="btn btn-primary"
            onClick={handleCreateNewThread}
            style={{ width: "100%", padding: "10px", fontSize: "13px" }}
          >
            <Plus size={16} />
            <span>New Thread</span>
          </button>
        </div>

        {/* Thread List */}
        <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
          {loadingConv ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
              Loading threads...
            </div>
          ) : conversations.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
              No chat history yet.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeConvId;
              const isEditing = conv.id === editingTitleId;

              return (
                <div
                  key={conv.id}
                  onClick={() => setActiveConvId(conv.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    marginBottom: "4px",
                    fontSize: "13px",
                    backgroundColor: isActive ? "rgba(59, 130, 246, 0.15)" : "transparent",
                    color: isActive ? "#93c5fd" : "var(--text-secondary)",
                    border: isActive ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid transparent",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden", flex: 1 }}>
                    <MessageSquare size={15} style={{ flexShrink: 0 }} />
                    {isEditing ? (
                      <input
                        type="text"
                        className="input-field"
                        value={newTitle}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => setNewTitle(e.target.value)}
                        style={{ padding: "2px 6px", fontSize: "12px", height: "26px" }}
                        autoFocus
                      />
                    ) : (
                      <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {conv.title}
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: "4px", marginLeft: "6px" }}>
                    {isEditing ? (
                      <>
                        <button
                          onClick={(e) => handleSaveTitle(conv.id, e)}
                          style={{ background: "none", border: "none", color: "#34d399", cursor: "pointer", padding: "2px" }}
                        >
                          <Check size={14} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingTitleId(null);
                          }}
                          style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", padding: "2px" }}
                        >
                          <X size={14} />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingTitleId(conv.id);
                            setNewTitle(conv.title);
                          }}
                          title="Rename thread"
                          style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "2px" }}
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          onClick={(e) => handleOpenDeleteModal(conv, e)}
                          title="Delete thread"
                          style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "2px" }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Workspace */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "var(--bg-primary)" }}>
        {/* Chat Area Header */}
        <div style={{
          height: "56px",
          borderBottom: "1px solid var(--border-color)",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "rgba(15, 23, 42, 0.5)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "15px", fontWeight: "600" }}>
              {activeConv ? activeConv.title : "New Conversation"}
            </h2>
          </div>

          {/* Document Filter Pill */}
          <div style={{ position: "relative" }}>
            <button
              className="btn btn-secondary"
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              style={{ padding: "6px 12px", fontSize: "12px" }}
            >
              <Filter size={13} />
              <span>
                {selectedDocIds.length === 0
                  ? "All Documents"
                  : `${selectedDocIds.length} Document(s) filtered`}
              </span>
            </button>

            {showFilterDropdown && (
              <div className="glass-card" style={{
                position: "absolute",
                right: 0,
                top: "40px",
                width: "280px",
                padding: "12px",
                zIndex: 60,
                maxHeight: "300px",
                overflowY: "auto",
              }}>
                <div style={{ fontSize: "12px", fontWeight: "600", marginBottom: "8px", color: "var(--text-secondary)" }}>
                  Grounding Scope
                </div>
                {allDocs.length === 0 ? (
                  <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>No completed documents available.</div>
                ) : (
                  allDocs.map((doc) => {
                    const isChecked = selectedDocIds.includes(doc.id);
                    return (
                      <label
                        key={doc.id}
                        style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 0", cursor: "pointer", fontSize: "12px" }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedDocIds([...selectedDocIds, doc.id]);
                            } else {
                              setSelectedDocIds(selectedDocIds.filter((id) => id !== doc.id));
                            }
                          }}
                        />
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {doc.original_filename}
                        </span>
                      </label>
                    );
                  })
                )}
                {selectedDocIds.length > 0 && (
                  <button
                    onClick={() => setSelectedDocIds([])}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--accent-blue)",
                      fontSize: "11px",
                      marginTop: "8px",
                      cursor: "pointer",
                      textDecoration: "underline",
                    }}
                  >
                    Clear Filter (Use All Documents)
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Inline Error Banner */}
        {chatError && (
          <AlertBanner
            variant="error"
            message={chatError}
            onClose={() => setChatError(null)}
            style={{ margin: "12px 24px 0" }}
          />
        )}

        {/* Message Stream */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
          {loadingMessages ? (
            <LoadingState label="Loading messages..." style={{ margin: "auto" }} />
          ) : messages.length === 0 ? (
            <EmptyState
              icon={<Sparkles size={24} />}
              title="Ask KnowledgeAI"
              description="Submit questions about your uploaded documents. KnowledgeAI will retrieve relevant passages and provide grounded answers with source citations."
            />
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === "user";

              return (
                <div
                  key={msg.id}
                  style={{
                    display: "flex",
                    justifyContent: isUser ? "flex-end" : "flex-start",
                  }}
                >
                  <div style={{
                    maxWidth: "75%",
                    borderRadius: "16px",
                    padding: "16px 20px",
                    backgroundColor: isUser ? "var(--accent-blue)" : "var(--bg-secondary)",
                    color: isUser ? "#ffffff" : "var(--text-primary)",
                    border: isUser ? "none" : "1px solid var(--border-color)",
                    boxShadow: "var(--shadow-md)",
                  }}>
                    <div style={{ whiteSpace: "pre-wrap", fontSize: "14px", lineHeight: "1.6" }}>
                      {msg.content}
                    </div>

                    {/* Citations Section */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div style={{
                        marginTop: "14px",
                        paddingTop: "12px",
                        borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                      }}>
                        <div style={{
                          fontSize: "11px",
                          fontWeight: "600",
                          textTransform: "uppercase",
                          letterSpacing: "0.5px",
                          color: "var(--text-muted)",
                          marginBottom: "6px",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}>
                          <FileText size={12} />
                          <span>Verified Citations:</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {msg.sources.map((cit, idx) => (
                            <button
                              key={idx}
                              className="citation-pill"
                              onClick={() => setSelectedCitation(cit)}
                              title="Click to view extracted source excerpt"
                            >
                              <FileText size={12} />
                              <span>{cit.filename}</span>
                              {cit.page_number && <span>(p. {cit.page_number})</span>}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {sending && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{
                borderRadius: "16px",
                padding: "14px 18px",
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-color)",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                color: "var(--text-secondary)",
                fontSize: "13px",
              }}>
                <div className="spinner" />
                <span>Searching knowledge base and generating answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--border-color)",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
        }}>
          <form
            onSubmit={handleSendMessage}
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: "12px",
              backgroundColor: "rgba(30, 41, 59, 0.8)",
              border: "1px solid var(--border-color)",
              borderRadius: "14px",
              padding: "10px 14px",
            }}
          >
            <textarea
              ref={textareaRef}
              rows={1}
              className="input-field"
              placeholder="Ask a question about your documents..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              style={{
                border: "none",
                background: "transparent",
                resize: "none",
                maxHeight: "120px",
                boxShadow: "none",
                padding: "4px 0",
              }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!inputQuery.trim() || sending}
              style={{ padding: "8px 14px", borderRadius: "8px" }}
            >
              <Send size={15} />
            </button>
          </form>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", textAlign: "center" }}>
            Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for newline. Answers are grounded in uploaded documents.
          </div>
        </div>
      </div>

      {/* Citation Details Modal */}
      <Modal
        isOpen={!!selectedCitation}
        onClose={() => setSelectedCitation(null)}
        title={selectedCitation?.filename}
        icon={<FileText size={20} color="var(--accent-blue)" />}
        maxWidth="600px"
      >
        {selectedCitation && (
          <div>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "14px" }}>
              {selectedCitation.page_number && <span>Page: {selectedCitation.page_number} • </span>}
              <span>Chunk Index: #{selectedCitation.chunk_index}</span>
              {selectedCitation.score && (
                <span> • Similarity: {(selectedCitation.score * 100).toFixed(1)}%</span>
              )}
            </div>

            <div style={{
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              padding: "16px",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
              fontFamily: "monospace",
              fontSize: "13px",
              lineHeight: "1.6",
              maxHeight: "300px",
              overflowY: "auto",
              color: "#e2e8f0",
              whiteSpace: "pre-wrap",
            }}>
              {selectedCitation.excerpt}
            </div>

            <div style={{ textAlign: "right", marginTop: "20px" }}>
              <button className="btn btn-secondary" onClick={() => setSelectedCitation(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Thread Confirmation Modal */}
      <ConfirmModal
        isOpen={!!convToDelete}
        title="Delete Conversation"
        message={`Are you sure you want to delete "${convToDelete?.title || "this conversation"}"? All messages and citations in this thread will be permanently deleted.`}
        confirmText="Delete Thread"
        cancelText="Cancel"
        variant="danger"
        icon="trash"
        isLoading={deletingConv}
        onCancel={() => {
          if (!deletingConv) setConvToDelete(null);
        }}
        onConfirm={handleConfirmDeleteConv}
      />
    </div>
  );
};


import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { AlertBanner, StatCard, StatusBadge } from "../components";
import {
  AdminOverviewData,
  AdminProviderOption,
  AdminSettingsData,
  AdminUserItem,
} from "../types";
import {
  ShieldAlert,
  Cpu,
  Database,
  Users,
  Files,
  Server,
  RefreshCw,
  Sliders,
  Check,
  UserCheck,
  UserX,
  Sparkles,
  Info,
} from "lucide-react";

export const AdminDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [overview, setOverview] = useState<AdminOverviewData | null>(null);
  const [settingsData, setSettingsData] = useState<AdminSettingsData | null>(null);
  const [usersList, setUsersList] = useState<AdminUserItem[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("gemini");
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingProvider, setUpdatingProvider] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const fetchAdminData = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const [overviewRes, settingsRes, usersRes] = await Promise.all([
        api.getAdminOverview(),
        api.getAdminSettings(),
        api.listAdminUsers(1, 50),
      ]);
      setOverview(overviewRes);
      setSettingsData(settingsRes);
      setSelectedProvider(settingsRes.active_chat_provider);
      setUsersList(usersRes.items);
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to load administrative console data.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleUpdateProvider = async () => {
    if (!selectedProvider || selectedProvider === settingsData?.active_chat_provider) {
      return;
    }
    setUpdatingProvider(true);
    setFeedback(null);
    try {
      const updated = await api.updateAdminChatProvider(selectedProvider);
      setSettingsData(updated);
      setSelectedProvider(updated.active_chat_provider);
      setFeedback({
        type: "success",
        message: `AI Chat Provider successfully switched to '${updated.active_chat_provider}'. Takes effect immediately!`,
      });
      // Refresh overview
      const newOverview = await api.getAdminOverview();
      setOverview(newOverview);
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to switch AI Chat Provider.",
      });
    } finally {
      setUpdatingProvider(false);
    }
  };

  const handleToggleUserStatus = async (targetUser: AdminUserItem) => {
    setActionLoadingId(targetUser.id);
    setFeedback(null);
    try {
      const newStatus = !targetUser.is_active;
      await api.toggleUserStatus(targetUser.id, newStatus);
      setUsersList((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: newStatus } : u))
      );
      setFeedback({
        type: "success",
        message: `Account for ${targetUser.email} is now ${newStatus ? "active" : "deactivated"}.`,
      });
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to modify user status.",
      });
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div style={{ padding: "32px 24px", maxWidth: "1240px", margin: "0 auto", width: "100%" }}>
      {/* Header Banner */}
      <div
        className="glass-card"
        style={{
          padding: "28px 32px",
          marginBottom: "28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          background: "linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span
              style={{
                fontSize: "11px",
                fontWeight: "700",
                textTransform: "uppercase",
                letterSpacing: "1px",
                backgroundColor: "rgba(239, 68, 68, 0.2)",
                color: "#f87171",
                padding: "3px 8px",
                borderRadius: "4px",
                border: "1px solid rgba(239, 68, 68, 0.3)",
              }}
            >
              ADMINISTRATOR CONSOLE
            </span>
            <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
              Authenticated as <strong>{user?.email}</strong>
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: "700" }}>System &amp; Infrastructure Administration</h1>
        </div>

        <button
          className="btn btn-secondary"
          onClick={fetchAdminData}
          disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <AlertBanner
          variant={feedback.type}
          message={feedback.message}
          onClose={() => setFeedback(null)}
          style={{ marginBottom: "24px" }}
        />
      )}

      {/* Infrastructure & Status Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "18px",
          marginBottom: "28px",
        }}
      >
        <StatCard
          title="System Status"
          value={overview?.infrastructure.status || "Ready"}
          subtext="Postgres, Redis & Vector Store"
          icon={<Server size={22} color="#34d399" />}
          iconBg="rgba(16, 185, 129, 0.15)"
          iconBorder="rgba(16, 185, 129, 0.3)"
          badge={<StatusBadge status={overview?.infrastructure.status || "ready"} size="sm" />}
        />

        <StatCard
          title="Platform Users"
          value={overview?.users.total || 0}
          subtext={`${overview?.users.active || 0} active accounts`}
          icon={<Users size={22} color="#60a5fa" />}
          iconBg="rgba(59, 130, 246, 0.15)"
          iconBorder="rgba(59, 130, 246, 0.3)"
        />

        <StatCard
          title="Total Documents"
          value={overview?.documents.total || 0}
          subtext={`${overview?.documents.chunks || 0} vector chunks in Qdrant`}
          icon={<Files size={22} color="#fbbf24" />}
          iconBg="rgba(245, 158, 11, 0.15)"
          iconBorder="rgba(245, 158, 11, 0.3)"
        />

        <StatCard
          title="Embedding Engine"
          value={settingsData?.active_embedding_provider || "gemini"}
          subtext={`Model: ${settingsData?.embedding_model || "gemini-embedding-001"}`}
          icon={<Database size={22} color="#a78bfa" />}
          iconBg="rgba(139, 92, 246, 0.15)"
          iconBorder="rgba(139, 92, 246, 0.3)"
        />
      </div>

      {/* AI CHAT PROVIDER SELECTION SECTION */}
      <div className="glass-card" style={{ padding: "28px", marginBottom: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px", marginBottom: "20px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <Cpu size={20} color="#60a5fa" />
              <h2 style={{ fontSize: "18px", fontWeight: "700" }}>Runtime AI Chat Provider Selection</h2>
            </div>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              Switch the active model for chat generation dynamically from this panel. Default backed by <code>.env</code> (<code>{settingsData?.env_default_chat_provider}</code>).
            </p>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleUpdateProvider}
            disabled={updatingProvider || selectedProvider === settingsData?.active_chat_provider}
            style={{ padding: "10px 20px" }}
          >
            {updatingProvider ? (
              <div className="spinner" />
            ) : (
              <>
                <Check size={16} />
                <span>Apply Selected Provider</span>
              </>
            )}
          </button>
        </div>

        {/* Options Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
          {settingsData?.providers.map((prov) => {
            const isCurrentActive = prov.id === settingsData.active_chat_provider;
            const isSelected = selectedProvider === prov.id;

            return (
              <div
                key={prov.id}
                onClick={() => setSelectedProvider(prov.id)}
                style={{
                  padding: "20px",
                  borderRadius: "12px",
                  border: isSelected
                    ? "2px solid var(--accent-blue)"
                    : "1px solid var(--border-color)",
                  backgroundColor: isSelected ? "rgba(59, 130, 246, 0.08)" : "rgba(15, 23, 42, 0.5)",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  position: "relative",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <input
                      type="radio"
                      name="chat_provider"
                      checked={isSelected}
                      onChange={() => setSelectedProvider(prov.id)}
                      style={{ cursor: "pointer", accentColor: "#3b82f6" }}
                    />
                    <span style={{ fontSize: "16px", fontWeight: "700" }}>{prov.name}</span>
                  </div>

                  <div style={{ display: "flex", gap: "6px" }}>
                    {isCurrentActive && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: "700",
                          backgroundColor: "rgba(16, 185, 129, 0.2)",
                          color: "#34d399",
                          padding: "2px 8px",
                          borderRadius: "4px",
                        }}
                      >
                        ACTIVE
                      </span>
                    )}
                    {prov.is_env_default && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: "700",
                          backgroundColor: "rgba(59, 130, 246, 0.2)",
                          color: "#60a5fa",
                          padding: "2px 8px",
                          borderRadius: "4px",
                        }}
                      >
                        ENV DEFAULT
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px" }}>
                  Model: <strong style={{ color: "var(--text-secondary)" }}>{prov.model}</strong>
                </div>

                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
                  {prov.description}
                </p>

                <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: prov.is_configured ? "#10b981" : "#f59e0b",
                    }}
                  />
                  <span style={{ color: prov.is_configured ? "#34d399" : "#fbbf24" }}>
                    {prov.is_configured ? "API Key Configured" : "Credentials Incomplete"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* USER MANAGEMENT SECTION */}
      <div className="glass-card" style={{ padding: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
          <Users size={20} color="#34d399" />
          <h2 style={{ fontSize: "18px", fontWeight: "700" }}>User Accounts &amp; Access Controls</h2>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)" }}>
                <th style={{ padding: "12px 16px" }}>Email</th>
                <th style={{ padding: "12px 16px" }}>Role</th>
                <th style={{ padding: "12px 16px" }}>Documents</th>
                <th style={{ padding: "12px 16px" }}>Joined</th>
                <th style={{ padding: "12px 16px" }}>Status</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {usersList.map((u) => {
                const isSelf = u.id === user?.id || u.email === user?.email;
                return (
                  <tr key={u.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <td style={{ padding: "14px 16px", fontWeight: "500" }}>
                      {u.email}
                      {isSelf && (
                        <span style={{ fontSize: "10px", color: "var(--accent-blue)", marginLeft: "6px" }}>
                          (You)
                        </span>
                      )}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      <StatusBadge
                        status={u.is_superuser || u.role === "admin" ? "admin" : "user"}
                        label={u.role ? u.role.toUpperCase() : u.is_superuser ? "ADMIN" : "USER"}
                        size="sm"
                      />
                    </td>
                    <td style={{ padding: "14px 16px", color: "var(--text-secondary)" }}>
                      {u.document_count} files
                    </td>
                    <td style={{ padding: "14px 16px", color: "var(--text-muted)" }}>
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      <StatusBadge
                        status={u.is_active ? "active" : "inactive"}
                        label={u.is_active ? "Active" : "Disabled"}
                        size="sm"
                      />
                    </td>
                    <td style={{ padding: "14px 16px", textAlign: "right" }}>
                      <button
                        onClick={() => handleToggleUserStatus(u)}
                        disabled={isSelf || actionLoadingId === u.id}
                        className={`btn ${u.is_active ? "btn-secondary" : "btn-primary"}`}
                        style={{
                          padding: "6px 12px",
                          fontSize: "12px",
                          opacity: isSelf ? 0.4 : 1,
                          cursor: isSelf ? "not-allowed" : "pointer",
                        }}
                        title={isSelf ? "You cannot modify your own administrator account." : undefined}
                      >
                        {actionLoadingId === u.id ? (
                          <div className="spinner" style={{ width: "14px", height: "14px" }} />
                        ) : u.is_active ? (
                          <>
                            <UserX size={14} />
                            <span>Deactivate</span>
                          </>
                        ) : (
                          <>
                            <UserCheck size={14} />
                            <span>Activate</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


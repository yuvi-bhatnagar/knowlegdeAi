import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AlertBanner } from "../components";
import { BookOpen, Lock, ShieldCheck, ArrowRight, CheckCircle2 } from "lucide-react";

interface SetPasswordPageProps {
  onSuccess?: () => void;
  onNavigateHome?: () => void;
}

export const SetPasswordPage: React.FC<SetPasswordPageProps> = ({ onSuccess, onNavigateHome }) => {
  const searchParams = new URLSearchParams(window.location.search);
  const token = searchParams.get("token") || "";
  const emailParam = searchParams.get("email") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(token ? null : "Missing activation token in URL. Please click the link received in your email.");
  const [loading, setLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const { setPassword: submitSetPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Missing activation token. Please request a new activation link.");
      return;
    }

    if (!password || !confirmPassword) {
      setError("Please fill in both password fields.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await submitSetPassword(token, password);
      setIsSuccess(true);
      if (onSuccess) {
        onSuccess();
      } else {
        // Clean URL parameter and navigate to root
        window.history.pushState(null, "", "/");
      }
    } catch (err: any) {
      setError(err.message || "Failed to activate account. The activation token may be expired or already used.");
    } finally {
      setLoading(false);
    }
  };

  const handleReturnHome = () => {
    if (onNavigateHome) {
      onNavigateHome();
    } else {
      window.history.pushState(null, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
      window.location.reload();
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background: "radial-gradient(ellipse at 50% 20%, rgba(30, 58, 138, 0.25) 0%, #0f172a 75%)",
      }}
    >
      <div className="glass-card" style={{ width: "100%", maxWidth: "440px", padding: "40px" }}>
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "56px",
              height: "56px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              marginBottom: "16px",
              boxShadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
            }}
          >
            <BookOpen size={30} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: "22px", fontWeight: "700", marginBottom: "8px" }}>
            Set Account Password
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
            {emailParam ? (
              <>
                Finalize registration for <strong style={{ color: "var(--text-primary)" }}>{emailParam}</strong>
              </>
            ) : (
              "Set your password to activate your KnowledgeAI workspace"
            )}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <AlertBanner
            variant="error"
            message={error}
            onClose={() => setError(null)}
            style={{ marginBottom: "20px" }}
          />
        )}

        {isSuccess ? (
          <div style={{ textAlign: "center", padding: "16px 0" }}>
            <CheckCircle2 size={48} color="#10b981" style={{ margin: "0 auto 16px auto" }} />
            <h3 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px" }}>Account Activated!</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "20px" }}>
              Your password has been successfully configured and your account is now active.
            </p>
            <button
              onClick={handleReturnHome}
              className="btn btn-primary"
              style={{ width: "100%", padding: "12px" }}
            >
              Go to Workspace
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "6px" }}>
                New Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="password"
                  className="input-field"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={!token || loading}
                  required
                  style={{ paddingLeft: "38px" }}
                />
                <Lock
                  size={16}
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-muted)",
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "6px" }}>
                Confirm Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="password"
                  className="input-field"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={!token || loading}
                  required
                  style={{ paddingLeft: "38px" }}
                />
                <ShieldCheck
                  size={16}
                  style={{
                    position: "absolute",
                    left: "12px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-muted)",
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={!token || loading}
              style={{ width: "100%", marginTop: "8px", padding: "12px" }}
            >
              {loading ? (
                <div className="spinner" />
              ) : (
                <>
                  <span>Activate & Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleReturnHome}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                cursor: "pointer",
                fontSize: "13px",
                marginTop: "8px",
                textAlign: "center",
              }}
            >
              ← Back to Sign In
            </button>
          </form>
        )}
      </div>
    </div>
  );
};


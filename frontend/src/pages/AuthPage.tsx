import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { SignupResponse } from "../types";
import { AlertBanner } from "../components";
import {
  BookOpen,
  Lock,
  Mail,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  ArrowLeft,
} from "lucide-react";

export const AuthPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [signupSuccess, setSignupSuccess] = useState<SignupResponse | null>(null);

  const { login, signup } = useAuth();

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    setLoading(true);
    try {
      const response = await signup(email);
      setSignupSuccess(response);
    } catch (err: any) {
      setError(err.message || "Failed to initiate signup. Please try again.");
    } finally {
      setLoading(false);
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
      <div className="glass-card" style={{ width: "100%", maxWidth: "460px", padding: "40px" }}>
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "56px",
              height: "56px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
              marginBottom: "16px",
              boxShadow: "0 8px 16px -4px rgba(59, 130, 246, 0.4)",
            }}
          >
            <BookOpen size={30} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: "700", marginBottom: "8px" }}>
            {signupSuccess
              ? "Check Your Inbox"
              : isRegister
              ? "Create KnowledgeAI Account"
              : "Welcome to KnowledgeAI"}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.5" }}>
            {signupSuccess
              ? `We have dispatched a secure activation link to ${signupSuccess.email}.`
              : isRegister
              ? "Enter your email to receive an activation link. You will set your password directly from your email."
              : "Sign in to access your grounded documents and chat history."}
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

        {/* Signup Success View */}
        {signupSuccess ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div
              style={{
                backgroundColor: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                padding: "20px",
                borderRadius: "12px",
                textAlign: "center",
              }}
            >
              <CheckCircle2 size={40} color="#10b981" style={{ margin: "0 auto 12px auto" }} />
              <div style={{ fontWeight: "600", fontSize: "15px", marginBottom: "6px" }}>
                Activation Link Dispatched
              </div>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                Click the link inside the email to set your password and complete account activation. The link expires in 24 hours.
              </p>
            </div>

            {/* Mailinator Direct Inbox Button */}
            {signupSuccess.mailinator_url && (
              <a
                href={signupSuccess.mailinator_url}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  padding: "12px",
                  backgroundColor: "rgba(59, 130, 246, 0.15)",
                  color: "#60a5fa",
                  borderColor: "rgba(59, 130, 246, 0.3)",
                  textDecoration: "none",
                }}
              >
                <span>Open Mailinator Inbox</span>
                <ExternalLink size={16} />
              </a>
            )}

            <button
              type="button"
              onClick={() => {
                setSignupSuccess(null);
                setEmail("");
                setPassword("");
                setIsRegister(false);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                cursor: "pointer",
                fontSize: "13px",
                marginTop: "4px",
              }}
            >
              <ArrowLeft size={14} />
              <span>Back to Sign In</span>
            </button>
          </div>
        ) : isRegister ? (
          /* Signup Form: Email only */
          <form onSubmit={handleSignUp} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "6px" }}>
                Email Address
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="email"
                  className="input-field"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{ paddingLeft: "38px" }}
                />
                <Mail
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
              disabled={loading}
              style={{ width: "100%", marginTop: "8px", padding: "12px" }}
            >
              {loading ? (
                <div className="spinner" />
              ) : (
                <>
                  <span>Send Activation Email</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        ) : (
          /* Sign In Form: Email and Password */
          <form onSubmit={handleSignIn} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "6px" }}>
                Email Address
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="email"
                  className="input-field"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{ paddingLeft: "38px" }}
                />
                <Mail
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
                Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: "100%", marginTop: "8px", padding: "12px" }}
            >
              {loading ? (
                <div className="spinner" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        )}

        {/* Switch Mode Toggle (only when not showing success screen) */}
        {!signupSuccess && (
          <div
            style={{
              textAlign: "center",
              marginTop: "24px",
              paddingTop: "20px",
              borderTop: "1px solid var(--border-color)",
            }}
          >
            <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              {isRegister ? "Already have an account?" : "Don't have an account yet?"}{" "}
              <button
                type="button"
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError(null);
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent-blue)",
                  cursor: "pointer",
                  fontWeight: "600",
                  textDecoration: "underline",
                }}
              >
                {isRegister ? "Sign In" : "Register with Email"}
              </button>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

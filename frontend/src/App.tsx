import React, { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Navbar } from "./components/Navbar";
import { AuthPage } from "./pages/AuthPage";
import { SetPasswordPage } from "./pages/SetPasswordPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ChatPage } from "./pages/ChatPage";

const MainLayout: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<"dashboard" | "documents" | "chat" | "admin">("dashboard");
  const [isSetPasswordRoute, setIsSetPasswordRoute] = useState<boolean>(() => {
    return (
      window.location.pathname.includes("set-password") ||
      window.location.search.includes("token=")
    );
  });

  const isAdmin = Boolean(user?.is_superuser || user?.role === "admin");

  useEffect(() => {
    const checkRoute = () => {
      setIsSetPasswordRoute(
        window.location.pathname.includes("set-password") ||
        window.location.search.includes("token=")
      );
    };

    window.addEventListener("popstate", checkRoute);
    return () => window.removeEventListener("popstate", checkRoute);
  }, []);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "16px",
          backgroundColor: "var(--bg-primary)",
          color: "var(--text-secondary)",
        }}
      >
        <div className="spinner" style={{ width: "32px", height: "32px", borderWidth: "3px" }} />
        <span style={{ fontSize: "14px" }}>Loading KnowledgeAI workspace...</span>
      </div>
    );
  }

  if (isSetPasswordRoute) {
    return (
      <SetPasswordPage
        onSuccess={() => {
          setIsSetPasswordRoute(false);
          window.history.pushState(null, "", "/");
        }}
        onNavigateHome={() => {
          setIsSetPasswordRoute(false);
          window.history.pushState(null, "", "/");
        }}
      />
    );
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === "dashboard" && <DashboardPage onNavigate={(tab) => setActiveTab(tab)} />}
        {activeTab === "documents" && <DocumentsPage />}
        {activeTab === "chat" && <ChatPage />}
        {activeTab === "admin" && (
          isAdmin ? <AdminDashboardPage /> : <DashboardPage onNavigate={(tab) => setActiveTab(tab)} />
        )}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
};

export default App;

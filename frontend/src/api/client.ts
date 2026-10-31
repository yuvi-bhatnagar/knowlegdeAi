import {
  AdminOverviewData,
  AdminSettingsData,
  AdminUserItem,
  ChatResponse,
  ConversationItem,
  DocumentItem,
  DocumentUploadResponse,
  MessageItem,
  PaginatedResponse,
  SignupResponse,
  TokenResponse,
  User,
} from "../types";

const API_BASE = "/api/v1";

class ApiError extends Error {
  status: number;
  code?: string;
  details?: any;

  constructor(message: string, status: number, code?: string, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options.headers || {});

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Do not set Content-Type for FormData (multipart/form-data)
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    if (response.status === 401) {
      // Discard token if expired or invalid
      localStorage.removeItem("access_token");
      window.dispatchEvent(new Event("auth-expired"));
    }
    const errorMessage =
      data?.error?.message || data?.detail || "An unexpected error occurred.";
    const errorCode = data?.error?.code || "HTTP_ERROR";
    throw new ApiError(errorMessage, response.status, errorCode, data?.error?.details);
  }

  return data as T;
}

export const api = {
  // Auth
  async signup(email: string): Promise<SignupResponse> {
    return request<SignupResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async setPassword(token: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/set-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    });
  },

  async register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async getMe(): Promise<User> {
    return request<User>("/auth/me");
  },

  async logout(): Promise<void> {
    try {
      await request("/auth/logout", { method: "POST" });
    } finally {
      localStorage.removeItem("access_token");
    }
  },

  // Documents
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentUploadResponse>("/documents/upload", {
      method: "POST",
      body: formData,
    });
  },

  async listDocuments(page = 1, pageSize = 20): Promise<PaginatedResponse<DocumentItem>> {
    return request<PaginatedResponse<DocumentItem>>(
      `/documents?page=${page}&page_size=${pageSize}`
    );
  },

  async getDocument(id: string): Promise<DocumentItem> {
    return request<DocumentItem>(`/documents/${id}`);
  },

  async deleteDocument(id: string): Promise<void> {
    return request<void>(`/documents/${id}`, { method: "DELETE" });
  },

  async retryDocument(id: string): Promise<DocumentItem> {
    return request<DocumentItem>(`/documents/${id}/retry`, { method: "POST" });
  },

  // Conversations
  async createConversation(title?: string): Promise<ConversationItem> {
    return request<ConversationItem>("/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  },

  async listConversations(page = 1, pageSize = 20): Promise<PaginatedResponse<ConversationItem>> {
    return request<PaginatedResponse<ConversationItem>>(
      `/conversations?page=${page}&page_size=${pageSize}`
    );
  },

  async updateConversation(id: string, title: string): Promise<ConversationItem> {
    return request<ConversationItem>(`/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  async deleteConversation(id: string): Promise<void> {
    return request<void>(`/conversations/${id}`, { method: "DELETE" });
  },

  async getMessages(conversationId: string, limit = 100): Promise<MessageItem[]> {
    return request<MessageItem[]>(`/conversations/${conversationId}/messages?limit=${limit}`);
  },

  // Chat
  async chat(
    question: string,
    conversationId?: string | null,
    documentIds?: string[] | null
  ): Promise<ChatResponse> {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({
        question,
        conversation_id: conversationId || null,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
      }),
    });
  },

  // Health
  async getHealthReady(): Promise<any> {
    return request<any>("/health/ready");
  },

  // Admin
  async getAdminOverview(): Promise<AdminOverviewData> {
    return request<AdminOverviewData>("/admin/overview");
  },

  async getAdminSettings(): Promise<AdminSettingsData> {
    return request<AdminSettingsData>("/admin/settings");
  },

  async updateAdminChatProvider(provider: string): Promise<AdminSettingsData> {
    return request<AdminSettingsData>("/admin/settings/ai-chat-provider", {
      method: "PATCH",
      body: JSON.stringify({ provider }),
    });
  },

  async listAdminUsers(page = 1, pageSize = 50): Promise<PaginatedResponse<AdminUserItem>> {
    return request<PaginatedResponse<AdminUserItem>>(`/admin/users?page=${page}&page_size=${pageSize}`);
  },

  async toggleUserStatus(userId: string, isActive: boolean): Promise<any> {
    return request<any>(`/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  },
};


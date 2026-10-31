export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser?: boolean;
  role?: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
}

export interface SignupResponse {
  message: string;
  email: string;
  mailinator_url?: string | null;
}

export interface DocumentItem {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  checksum: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  error_summary?: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  original_filename: string;
  status: string;
  message: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number?: number | null;
  chunk_index: number;
  excerpt: string;
  score?: number | null;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources: Citation[];
  token_usage?: Record<string, any> | null;
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  conversation_id: string;
  message_id: string;
  citations: Citation[];
  model_used: string;
  insufficient_evidence: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminProviderOption {
  id: string;
  name: string;
  model: string;
  is_configured: boolean;
  is_active: boolean;
  is_env_default: boolean;
  description: string;
}

export interface AdminSettingsData {
  active_chat_provider: string;
  env_default_chat_provider: string;
  active_embedding_provider: string;
  embedding_model: string;
  email_provider: string;
  providers: AdminProviderOption[];
}

export interface AdminOverviewData {
  users: { total: number; active: number };
  documents: { total: number; chunks: number };
  chat: {
    conversations: number;
    messages: number;
    active_chat_provider: string;
    env_default_chat_provider: string;
    active_embedding_provider: string;
  };
  infrastructure: {
    status: string;
    database: string;
    vector_store: string;
    cache_broker: string;
    email_provider: string;
  };
}

export interface AdminUserItem {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  created_at: string;
  document_count: number;
}



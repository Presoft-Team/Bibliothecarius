export interface Folder {
  id: string;
  name: string;
  parent_folder_id: string | null;
}

export interface Document {
  id: string;
  folder_id: string | null;
  filename: string;
  content_type: string;
  status: string;
  uploaded_at: string;
}

export interface DocumentPage {
  page_number: number;
  extracted_text: string;
  extraction_method: "native" | "ocr_fallback";
  confidence: number;
}

export interface DocumentPreview {
  document: Document;
  pages: DocumentPage[];
}

export interface DocumentConfirmResult {
  document: Document;
  chunk_count: number;
}

export interface Tone {
  id: string;
  name: string;
  description: string;
  system_prompt_template: string;
  params: Record<string, unknown>;
  is_default: boolean;
  created_at: string;
}

export type LLMProvider = "ollama" | "anthropic" | "openai" | "gemini";

export interface AssistantConfig {
  id: string;
  name: string;
  persona_description: string;
  default_tone_id: string | null;
  default_provider: LLMProvider;
  default_model: string;
  temperature: number;
  max_context_chunks: number;
  params: Record<string, unknown>;
}

export type CloudProvider = "anthropic" | "openai" | "gemini";

export interface ProviderCredential {
  provider: CloudProvider;
  key_hint: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  tone_id: string | null;
  provider: string;
  model: string;
  title: string | null;
  created_at: string;
}

export interface RetrievalScope {
  type: "all" | "folders";
  folder_ids?: string[] | null;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_ref: number | null;
  chunk_text: string;
  distance: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrieval_scope: RetrievalScope;
  scope_fallback_used: boolean;
  source_chunk_ids: string[];
  citations: Citation[];
  created_at: string;
}

export interface ChatTurn {
  user_message: Message;
  assistant_message: Message;
}

export interface CurrentUser {
  id: string;
  display_name: string;
  email: string;
  role: "user" | "admin";
}

export interface AdminUser {
  keycloak_id: string;
  username: string;
  email: string | null;
  enabled: boolean;
  roles: string[];
  provisioned: boolean;
}

export interface AdminUserInviteResult {
  keycloak_id: string;
  username: string;
  email: string;
  temporary_password: string;
}

export interface OllamaPullStatus {
  status: "pulling" | "success" | "error" | "not_found";
  completed: number;
  total: number;
  error: string | null;
}

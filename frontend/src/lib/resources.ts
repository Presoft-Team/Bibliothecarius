import { api } from "./api";
import type {
  AdminUser,
  AdminUserInviteResult,
  AssistantConfig,
  ChatTurn,
  Conversation,
  CurrentUser,
  Document,
  DocumentConfirmResult,
  DocumentPreview,
  Folder,
  Message,
  OllamaPullStatus,
  ProviderCredential,
  RetrievalScope,
  Tone,
} from "./types";

export const llmApi = {
  listModels: (provider: string) =>
    api.get<string[]>("/llm/models", { params: { provider } }).then((r) => r.data),
  pullOllamaModel: (name: string) =>
    api.post<OllamaPullStatus>("/llm/ollama/models", { name }).then((r) => r.data),
  ollamaPullStatus: (name: string) =>
    api.get<OllamaPullStatus>(`/llm/ollama/models/${encodeURIComponent(name)}/status`).then((r) => r.data),
  removeOllamaModel: (name: string) => api.delete(`/llm/ollama/models/${encodeURIComponent(name)}`),
};

export const meApi = {
  get: () => api.get<CurrentUser>("/me").then((r) => r.data),
};

export const foldersApi = {
  list: () => api.get<Folder[]>("/folders").then((r) => r.data),
  create: (name: string, parent_folder_id?: string | null) =>
    api.post<Folder>("/folders", { name, parent_folder_id }).then((r) => r.data),
  update: (id: string, payload: { name?: string; parent_folder_id?: string | null }) =>
    api.patch<Folder>(`/folders/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/folders/${id}`),
};

export const documentsApi = {
  list: (params?: { folder_id?: string; unfiled?: boolean }) =>
    api.get<Document[]>("/documents", { params }).then((r) => r.data),
  upload: (file: File, folder_id?: string | null) => {
    const form = new FormData();
    form.append("file", file);
    const params = folder_id ? { folder_id } : undefined;
    return api.post<Document>("/documents", form, { params }).then((r) => r.data);
  },
  preview: (id: string) => api.get<DocumentPreview>(`/documents/${id}/preview`).then((r) => r.data),
  confirm: (id: string) =>
    api.post<DocumentConfirmResult>(`/documents/${id}/confirm`).then((r) => r.data),
  move: (id: string, folder_id: string | null) =>
    api.patch<Document>(`/documents/${id}`, { folder_id }).then((r) => r.data),
  remove: (id: string) => api.delete(`/documents/${id}`),
};

export const tonesApi = {
  list: () => api.get<Tone[]>("/tones").then((r) => r.data),
  create: (payload: {
    name: string;
    description?: string;
    system_prompt_template: string;
    params?: Record<string, unknown>;
    is_default?: boolean;
  }) => api.post<Tone>("/tones", payload).then((r) => r.data),
  update: (
    id: string,
    payload: Partial<{
      name: string;
      description: string;
      system_prompt_template: string;
      params: Record<string, unknown>;
      is_default: boolean;
    }>
  ) => api.patch<Tone>(`/tones/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/tones/${id}`),
};

export const assistantConfigApi = {
  get: () => api.get<AssistantConfig>("/assistant-config").then((r) => r.data),
  update: (payload: Partial<Omit<AssistantConfig, "id">>) =>
    api.patch<AssistantConfig>("/assistant-config", payload).then((r) => r.data),
};

export const providerCredentialsApi = {
  list: () => api.get<ProviderCredential[]>("/provider-credentials").then((r) => r.data),
  set: (provider: string, api_key: string) =>
    api.put<ProviderCredential>(`/provider-credentials/${provider}`, { api_key }).then((r) => r.data),
  remove: (provider: string) => api.delete(`/provider-credentials/${provider}`),
};

export const chatApi = {
  listConversations: () => api.get<Conversation[]>("/conversations").then((r) => r.data),
  createConversation: (payload: { tone_id?: string | null; provider?: string; model?: string }) =>
    api.post<Conversation>("/conversations", payload).then((r) => r.data),
  listMessages: (conversationId: string) =>
    api.get<Message[]>(`/conversations/${conversationId}/messages`).then((r) => r.data),
  sendMessage: (conversationId: string, content: string, retrieval_scope: RetrievalScope) =>
    api
      .post<ChatTurn>(`/conversations/${conversationId}/messages`, { content, retrieval_scope })
      .then((r) => r.data),
  deleteConversation: (conversationId: string) => api.delete(`/conversations/${conversationId}`),
  renameConversation: (conversationId: string, title: string) =>
    api.patch<Conversation>(`/conversations/${conversationId}`, { title }).then((r) => r.data),
};

export const adminUsersApi = {
  list: () => api.get<AdminUser[]>("/admin/users").then((r) => r.data),
  invite: (username: string, email: string, temporary_password: string) =>
    api
      .post<AdminUserInviteResult>("/admin/users", { username, email, temporary_password })
      .then((r) => r.data),
  grantRole: (keycloakId: string, role: string) =>
    api.put<AdminUser>(`/admin/users/${keycloakId}/roles/${role}`).then((r) => r.data),
  revokeRole: (keycloakId: string, role: string) =>
    api.delete<AdminUser>(`/admin/users/${keycloakId}/roles/${role}`).then((r) => r.data),
};

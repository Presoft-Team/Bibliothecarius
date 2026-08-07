import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Info, MessageSquarePlus, Pencil, Plus, SendHorizontal, Settings2, Trash2 } from "lucide-react";
import { chatApi, foldersApi, tonesApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import ModelPicker from "../components/ModelPicker";
import ErrorNotice from "../components/ErrorNotice";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import Field, { inputClass } from "../components/ui/Field";
import type { Conversation, Folder, Message, Tone } from "../lib/types";

function conversationLabel(c: Conversation): string {
  return c.title || `${c.provider}/${c.model}`;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [expandedCitations, setExpandedCitations] = useState<string | null>(null);
  const [tones, setTones] = useState<Tone[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [showNewConversationForm, setShowNewConversationForm] = useState(false);

  const [newTone, setNewTone] = useState<string>("");
  const [newProvider, setNewProvider] = useState("ollama");
  const [newModel, setNewModel] = useState("");

  const [scopeType, setScopeType] = useState<"all" | "folders">("all");
  const [scopeFolderIds, setScopeFolderIds] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  // The sidebar row and the header both render an inline editor for the active conversation —
  // without this, renaming the active chat mounted two autoFocus inputs at once, each stealing
  // focus from the other and immediately blur-committing before the user could type anything.
  const [renameSource, setRenameSource] = useState<"sidebar" | "header" | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatApi.listConversations().then(setConversations);
    tonesApi.list().then(setTones);
    foldersApi.list().then(setFolders);
  }, []);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    chatApi.listMessages(activeId).then(setMessages);
  }, [activeId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pendingMessage, sending]);

  const addConversation = async (payload: { tone_id?: string; provider?: string; model?: string }) => {
    const conv = await chatApi.createConversation(payload);
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
  };

  // One click, no picker — uses the assistant's own defaults end to end.
  const newChat = () => addConversation({});

  const startCustomConversation = () => {
    addConversation({
      tone_id: newTone || undefined,
      provider: newProvider || undefined,
      model: newModel || undefined,
    });
    setShowNewConversationForm(false);
  };

  const toggleScopeFolder = (id: string) => {
    setScopeFolderIds((prev) => (prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]));
  };

  const deleteConversation = async (id: string) => {
    if (!confirm("Delete this conversation and its message history?")) return;
    await chatApi.deleteConversation(id);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  };

  const startRename = (c: Conversation, source: "sidebar" | "header") => {
    setRenamingId(c.id);
    setRenameSource(source);
    setRenameValue(conversationLabel(c));
  };

  const commitRename = async () => {
    if (!renamingId) return;
    const id = renamingId;
    const title = renameValue.trim();
    setRenamingId(null);
    setRenameSource(null);
    if (!title) return;
    const updated = await chatApi.renameConversation(id, title);
    setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)));
  };

  const send = async () => {
    if (!activeId || !draft.trim()) return;
    const content = draft.trim();
    setSending(true);
    setError(null);
    setPendingMessage(content);
    setDraft("");
    const isFirstMessage = messages.length === 0;
    const scope =
      scopeType === "folders" && scopeFolderIds.length > 0
        ? { type: "folders" as const, folder_ids: scopeFolderIds }
        : { type: "all" as const };

    try {
      const turn = await chatApi.sendMessage(activeId, content, scope);
      setMessages((prev) => [...prev, turn.user_message, turn.assistant_message]);
      // Mirrors the backend's auto-title-from-first-message so the sidebar updates immediately
      // instead of waiting for the next full conversation list reload.
      if (isFirstMessage) {
        const autoTitle = content.slice(0, 60);
        setConversations((prev) =>
          prev.map((c) => (c.id === activeId && !c.title ? { ...c, title: autoTitle } : c))
        );
      }
    } catch (err) {
      setError(getErrorMessage(err, "The assistant couldn't respond — check the provider/model and API key are valid."));
      setDraft(content); // don't make the user retype it after a failed send
    } finally {
      setSending(false);
      setPendingMessage(null);
    }
  };

  const activeConversation = conversations.find((c) => c.id === activeId);

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-6">
      <aside className="flex w-72 shrink-0 flex-col gap-4">
        <Button variant="primary" className="w-full" onClick={newChat}>
          <Plus className="h-4 w-4" />
          New Chat
        </Button>

        <div className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                activeId === c.id
                  ? "bg-accent-50 dark:bg-accent-900/40"
                  : "hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {renamingId === c.id && renameSource === "sidebar" ? (
                <input
                  name="conversation-title-sidebar"
                  autoFocus
                  className={`${inputClass} min-w-0 flex-1 py-1`}
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onBlur={commitRename}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") commitRename();
                    if (e.key === "Escape") {
                      setRenamingId(null);
                      setRenameSource(null);
                    }
                  }}
                />
              ) : (
                <button className="min-w-0 flex-1 text-left" onClick={() => setActiveId(c.id)}>
                  <div className="truncate font-medium text-slate-700 dark:text-slate-200">
                    {conversationLabel(c)}
                  </div>
                  <div className="text-xs text-slate-400">{new Date(c.created_at).toLocaleString()}</div>
                </button>
              )}
              {!(renamingId === c.id && renameSource === "sidebar") && (
                <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100">
                  <button
                    className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600 dark:hover:bg-slate-700"
                    title="Rename conversation"
                    onClick={() => startRename(c, "sidebar")}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                    title="Delete conversation"
                    onClick={() => deleteConversation(c.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </div>
          ))}
          {conversations.length === 0 && (
            <p className="px-3 text-sm text-slate-400">No conversations yet.</p>
          )}
        </div>

        <div>
          <button
            className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            onClick={() => setShowNewConversationForm((v) => !v)}
          >
            <Settings2 className="h-3.5 w-3.5" />
            {showNewConversationForm ? "Hide options" : "Customize tone / provider / model"}
          </button>

          {showNewConversationForm && (
            <Card className="mt-2">
              <Field label="Tone">
                <select
                  name="new-conversation-tone"
                  className={inputClass}
                  value={newTone}
                  onChange={(e) => setNewTone(e.target.value)}
                >
                  <option value="">Assistant default</option>
                  {tones.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Provider">
                <select
                  name="new-conversation-provider"
                  className={inputClass}
                  value={newProvider}
                  onChange={(e) => {
                    setNewProvider(e.target.value);
                    setNewModel("");
                  }}
                >
                  <option value="ollama">Ollama (local)</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                </select>
              </Field>
              <Field label="Model">
                <ModelPicker provider={newProvider} value={newModel} onChange={setNewModel} allowBlank />
              </Field>
              <Button variant="primary" className="w-full" onClick={startCustomConversation}>
                Start conversation
              </Button>
            </Card>
          )}
        </div>
      </aside>

      <Card className="flex min-w-0 flex-1 flex-col p-0">
        {!activeId ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
            <MessageSquarePlus className="h-10 w-10 text-slate-300 dark:text-slate-600" />
            <div>
              <p className="font-medium text-slate-600 dark:text-slate-300">Start a new chat, or pick one up</p>
              <p className="text-sm text-slate-400">Your questions are answered using your uploaded documents.</p>
            </div>
            <Button variant="primary" onClick={newChat}>
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
            {conversations.length > 0 && (
              <div className="w-full max-w-xs">
                <p className="mb-1.5 text-xs font-semibold text-slate-400">Or continue a previous chat</p>
                <div className="space-y-1">
                  {conversations.slice(0, 4).map((c) => (
                    <button
                      key={c.id}
                      className="w-full truncate rounded-lg border border-slate-200 px-3 py-1.5 text-left text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                      onClick={() => setActiveId(c.id)}
                    >
                      {conversationLabel(c)}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3 dark:border-slate-800">
              {renamingId === activeConversation?.id && renameSource === "header" ? (
                <input
                  name="conversation-title-header"
                  autoFocus
                  className={`${inputClass} max-w-xs py-1`}
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onBlur={commitRename}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") commitRename();
                    if (e.key === "Escape") {
                      setRenamingId(null);
                      setRenameSource(null);
                    }
                  }}
                />
              ) : (
                <button
                  className="group flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-200"
                  onClick={() => activeConversation && startRename(activeConversation, "header")}
                >
                  {activeConversation ? conversationLabel(activeConversation) : ""}
                  <Pencil className="h-3 w-3 text-slate-300 opacity-0 group-hover:opacity-100" />
                </button>
              )}
              <span className="text-xs text-slate-400">
                {activeConversation?.provider}/{activeConversation?.model}
              </span>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[75%] ${m.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                    {(m.scope_fallback_used || m.citations.length > 0) && (
                      <div className="flex items-center gap-1.5">
                        {m.scope_fallback_used && (
                          <Badge variant="warn">searched all documents</Badge>
                        )}
                        {m.citations.length > 0 && (
                          <button
                            className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                            onClick={() => setExpandedCitations(expandedCitations === m.id ? null : m.id)}
                          >
                            <Info className="h-3 w-3" />
                            {m.citations.length} source{m.citations.length > 1 ? "s" : ""}
                          </button>
                        )}
                      </div>
                    )}
                    <div
                      className={`rounded-2xl px-4 py-2.5 text-sm ${
                        m.role === "user"
                          ? "rounded-br-sm bg-accent-600 text-white"
                          : "rounded-bl-sm border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
                      }`}
                    >
                      {m.role === "assistant" ? (
                        <div className="markdown-body">
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      )}
                    </div>
                    {expandedCitations === m.id && (
                      <div className="rounded-lg bg-slate-50 p-2 text-xs text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                        {m.citations
                          .map((c) => c.filename + (c.page_ref ? ` (p.${c.page_ref})` : ""))
                          .join(", ")}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {pendingMessage && (
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl rounded-br-sm bg-accent-600 px-4 py-2.5 text-sm text-white">
                    <p className="whitespace-pre-wrap">{pendingMessage}</p>
                  </div>
                </div>
              )}
              {sending && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-slate-200 p-4 dark:border-slate-800">
              <div className="mb-2 flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                <label className="flex items-center gap-1.5">
                  <input
                    type="radio"
                    name="retrieval-scope"
                    checked={scopeType === "all"}
                    onChange={() => setScopeType("all")}
                  />
                  All documents
                </label>
                <label className="flex items-center gap-1.5">
                  <input
                    type="radio"
                    name="retrieval-scope"
                    checked={scopeType === "folders"}
                    onChange={() => setScopeType("folders")}
                  />
                  Specific folders
                </label>
                {scopeType === "folders" &&
                  folders.map((f) => (
                    <label key={f.id} className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        name={`scope-folder-${f.id}`}
                        checked={scopeFolderIds.includes(f.id)}
                        onChange={() => toggleScopeFolder(f.id)}
                      />
                      {f.name}
                    </label>
                  ))}
                {scopeType === "folders" && folders.length === 0 && <span>No folders yet.</span>}
              </div>

              {error && <div className="mb-2">
                <ErrorNotice message={error} />
              </div>}

              <div className="flex items-end gap-2">
                <textarea
                  name="chat-message"
                  className={`${inputClass} resize-none`}
                  rows={2}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  placeholder="Ask a question…"
                />
                <Button variant="primary" disabled={sending || !draft.trim()} onClick={send}>
                  <SendHorizontal className="h-4 w-4" />
                  Send
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

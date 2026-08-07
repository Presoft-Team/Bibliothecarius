import { useEffect, useRef, useState } from "react";
import { FileUp, FolderOpen, Trash2, X } from "lucide-react";
import { documentsApi, foldersApi } from "../lib/resources";
import { getErrorMessage } from "../lib/errors";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import { inputClass } from "../components/ui/Field";
import type { Document, DocumentPreview, Folder } from "../lib/types";

type ViewScope = { kind: "all" } | { kind: "unfiled" } | { kind: "folder"; folderId: string };

export default function DocumentsPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [scope, setScope] = useState<ViewScope>({ kind: "all" });
  const [newFolderName, setNewFolderName] = useState("");
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFolders = () => foldersApi.list().then(setFolders);

  const loadDocuments = (s: ViewScope) => {
    const params =
      s.kind === "folder" ? { folder_id: s.folderId } : s.kind === "unfiled" ? { unfiled: true } : undefined;
    documentsApi.list(params).then(setDocuments);
  };

  useEffect(() => {
    loadFolders();
  }, []);
  useEffect(() => loadDocuments(scope), [scope]);

  // Extraction runs in the background after upload; poll briefly while anything is still processing.
  useEffect(() => {
    if (!documents.some((d) => d.status === "uploaded")) return;
    const timer = setInterval(() => loadDocuments(scope), 2000);
    return () => clearInterval(timer);
  }, [documents, scope]);

  const openPreview = (id: string) => {
    setSelectedDoc(id);
    documentsApi.preview(id).then(setPreview);
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    await foldersApi.create(newFolderName.trim());
    setNewFolderName("");
    loadFolders();
  };

  const handleDeleteFolder = async (id: string) => {
    if (!confirm("Delete this folder? Documents inside become unfiled.")) return;
    await foldersApi.remove(id);
    if (scope.kind === "folder" && scope.folderId === id) setScope({ kind: "all" });
    loadFolders();
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);
    const targetFolder = scope.kind === "folder" ? scope.folderId : null;
    try {
      for (const file of Array.from(files)) {
        await documentsApi.upload(file, targetFolder);
      }
      loadDocuments(scope);
    } catch (err) {
      setError(getErrorMessage(err, "Upload failed — check the file type is supported (pdf, docx, xlsx, txt)"));
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleConfirm = async (id: string) => {
    await documentsApi.confirm(id);
    loadDocuments(scope);
    if (selectedDoc === id) openPreview(id);
  };

  const handleMove = async (id: string, folderId: string) => {
    await documentsApi.move(id, folderId || null);
    loadDocuments(scope);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document?")) return;
    await documentsApi.remove(id);
    if (selectedDoc === id) {
      setSelectedDoc(null);
      setPreview(null);
    }
    loadDocuments(scope);
  };

  const navButtonClass = (active: boolean) =>
    `flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
      active
        ? "bg-accent-50 text-accent-700 dark:bg-accent-900/40 dark:text-accent-300"
        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
    }`;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Documents</h1>

      <div className="flex items-start gap-6">
        <Card className="w-64 shrink-0">
          <h2 className="mb-2 text-sm font-semibold text-slate-500 dark:text-slate-400">Folders</h2>
          <div className="space-y-0.5">
            <button className={`${navButtonClass(scope.kind === "all")} w-full`} onClick={() => setScope({ kind: "all" })}>
              All documents
            </button>
            <button
              className={`${navButtonClass(scope.kind === "unfiled")} w-full`}
              onClick={() => setScope({ kind: "unfiled" })}
            >
              Unfiled
            </button>
            {folders.map((f) => (
              <div key={f.id} className="group flex items-center gap-1">
                <button
                  className={`${navButtonClass(scope.kind === "folder" && scope.folderId === f.id)} min-w-0 flex-1`}
                  onClick={() => setScope({ kind: "folder", folderId: f.id })}
                >
                  <FolderOpen className="h-4 w-4 shrink-0" />
                  <span className="min-w-0 truncate">{f.name}</span>
                </button>
                <button
                  className="shrink-0 rounded p-1.5 text-slate-400 opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 dark:hover:bg-red-950/40"
                  onClick={() => handleDeleteFolder(f.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-1.5">
            <input
              name="new-folder-name"
              className={inputClass}
              placeholder="New folder"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
            />
            <Button onClick={handleCreateFolder}>Add</Button>
          </div>
        </Card>

        <Card className="min-w-0 flex-1">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400">
              {scope.kind === "all"
                ? "All documents"
                : scope.kind === "unfiled"
                ? "Unfiled documents"
                : folders.find((f) => f.id === scope.folderId)?.name ?? "Folder"}
            </h2>
            <label>
              <Button variant="primary" className="cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                <FileUp className="h-4 w-4" />
                Upload
              </Button>
              <input
                name="document-upload"
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.xlsx,.xls,.txt"
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
            </label>
          </div>
          {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

          <div className="space-y-1">
            {documents.length === 0 && <p className="text-sm text-slate-400">No documents here yet.</p>}
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <button
                  className="flex min-w-0 flex-1 items-center gap-2 text-left text-sm text-slate-700 dark:text-slate-200"
                  onClick={() => openPreview(doc.id)}
                >
                  <span className="min-w-0 truncate">{doc.filename}</span>
                  <span className="shrink-0">
                    <Badge variant={doc.status === "ingested" ? "accent" : "warn"}>{doc.status}</Badge>
                  </span>
                </button>
                <select
                  name={`move-folder-${doc.id}`}
                  className={`${inputClass} !w-32 shrink-0 py-1 text-xs`}
                  value={doc.folder_id ?? ""}
                  onChange={(e) => handleMove(doc.id, e.target.value)}
                  title="Move to folder"
                >
                  <option value="">Unfiled</option>
                  {folders.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
                <button
                  className="shrink-0 rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                  onClick={() => handleDelete(doc.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </Card>

        {selectedDoc && preview && (
          <Card className="w-96 shrink-0">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-700 dark:text-slate-200">
                {preview.document.filename}
              </h2>
              <button
                className="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                onClick={() => setSelectedDoc(null)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
              Status: {preview.document.status}. Review extracted text below before confirming — pages
              marked "ocr_fallback" or with low confidence may need a closer look (e.g. a scanned page
              that OCR misread).
            </p>

            <div className="max-h-96 space-y-2 overflow-y-auto">
              {preview.pages.map((p) => (
                <div key={p.page_number} className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                  <div className="mb-1 flex items-center justify-between">
                    <strong className="text-sm">Page {p.page_number}</strong>
                    <Badge variant={p.extraction_method === "ocr_fallback" ? "warn" : "default"}>
                      {p.extraction_method} · {(p.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <p className="whitespace-pre-wrap text-xs text-slate-600 dark:text-slate-400">
                    {p.extracted_text || <em className="text-slate-400">No text extracted</em>}
                  </p>
                </div>
              ))}
              {preview.pages.length === 0 && (
                <p className="text-sm text-slate-400">Extraction still in progress…</p>
              )}
            </div>

            {preview.document.status === "previewing" && (
              <Button variant="primary" className="mt-3 w-full" onClick={() => handleConfirm(preview.document.id)}>
                Confirm & ingest
              </Button>
            )}
            {preview.document.status === "ingested" && (
              <p className="mt-3 text-xs text-slate-400">Already ingested into the knowledge base.</p>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

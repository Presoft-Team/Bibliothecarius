# Bibliothecarius — Local RAG Chat Platform

A self-hosted chat platform where users upload documents (PDF, Word, Excel, TXT) and chat with an
AI that answers using retrieved content from those documents. Supports configurable AI "tones",
folder-organized documents, per-user assistant settings, and a choice of local (Ollama) or cloud
(Claude/GPT/Gemini) LLM providers.

See the architecture plan for full design details.

## Stack

- Backend: Python + FastAPI
- Frontend: React + TypeScript (Vite)
- Database: PostgreSQL + pgvector
- Auth: self-hosted Keycloak (OIDC)
- Local LLM runtime: Ollama
- Doc extraction: pypdf / python-docx / openpyxl + Tesseract OCR fallback

## Status

Feature-complete end to end: auth, the document pipeline, tones + assistant config CRUD, the LLM
provider abstraction, chat (retrieval + folder-scoped fallback + history + citations), admin user
management, and a working frontend wired to all of it.

### Frontend

- `src/lib/resources.ts` — typed API client functions for every backend resource; `src/lib/types.ts`
  mirrors the backend Pydantic schemas.
- `src/lib/AuthContext.tsx` — fetches `/me` once after Keycloak login and exposes the user's role;
  the "Users" nav link and page are gated on `role === "admin"` (the backend also enforces this
  independently, so the frontend gate is convenience, not the security boundary).
- **Chat** — conversation list/create (tone/provider/model pickers), message thread with citations
  and a visible badge when the folder-scoped fallback fires.
- **Documents** — folder list (create/delete) with an All/Unfiled/per-folder view, multi-file
  upload, a preview panel showing each page's extraction method and confidence (flagging
  `ocr_fallback` pages) with a confirm-to-ingest step, move-between-folders, delete. Polls briefly
  after upload while background extraction finishes.
- **Tones** — list/create/edit; "Save changes" (PATCH, replace) vs. "Save as new" (POST) map
  directly to the two buttons next to each other in the edit form.
- **Assistant Settings** — persona/model/provider form plus cloud provider API key management
  (add/remove; keys are never echoed back, matching the backend).
- **Users** (admin-only) — list with roles and "never logged in" status, invite (returns a
  temporary password to hand off out of band), grant/revoke admin role.
- No visual/browser verification was performed in this environment — coverage here is a clean
  `tsc -b && vite build`, an API-shape audit against the backend schemas, and live smoke tests of
  every endpoint each page calls on load (200s, correct CORS preflight). Click through it once
  yourself before relying on it.

### Tones & assistant config

- `POST/GET/PATCH/DELETE /tones` — each tone has a `system_prompt_template` and a free-form `params`
  JSON blob (formality, verbosity, persona traits, etc.). Only one tone per user can have
  `is_default: true`; setting it on one tone automatically clears it on the others. "Save as new"
  is just `POST` with a fresh name; "replace" is `PATCH` on the existing tone's id.
- `GET/PATCH /assistant-config` — single settings row per user (auto-created with defaults on first
  `GET`), covering assistant name/persona, default tone, default LLM provider + model, temperature,
  and max retrieved chunks. `default_provider` is validated against `ollama | anthropic | openai |
  gemini`, and `default_tone_id` must reference one of the user's own tones.

### LLM providers

- Common interface in `app/services/llm/base.py`; adapters for Ollama (local, no key needed),
  Anthropic, OpenAI, and Gemini live alongside it. `app/services/llm/factory.py` picks the right one
  and, for cloud providers, loads + decrypts the user's stored API key.
- `PUT/DELETE /provider-credentials/{provider}` (`anthropic | openai | gemini`) stores a user's own
  API key, encrypted at rest with `SECRET_ENCRYPTION_KEY` (Fernet). `GET /provider-credentials` lists
  which providers have a key on file — it never returns the key itself.
- `POST /llm/test` exercises the abstraction directly (`{provider, model, message}` →
  `{reply}`) ahead of the chat endpoint reusing the same factory with retrieved context. A cloud
  call with no stored key fails clearly (502, "no API key on file") rather than crashing.
- For local generation, pull a chat model into Ollama once per fresh `ollama_data` volume, e.g.
  `docker compose exec ollama ollama pull qwen2.5:0.5b` for something small/fast, or a larger model
  for real use.

### Chat

- `POST /conversations` (`{tone_id?, provider?, model?}`, all optional — falls back to the user's
  assistant config defaults) → `GET /conversations` → `GET /conversations/{id}/messages` →
  `POST /conversations/{id}/messages` (`{content, retrieval_scope?}`) runs retrieval, assembles a
  system prompt from the conversation's tone + assistant config + retrieved chunks, calls the LLM,
  and persists both turns. Returns `{user_message, assistant_message, citations}`.
- `retrieval_scope` is `{"type": "all"}` (default) or `{"type": "folders", "folder_ids": [...]}`.
  Folder-scoped requests that come back with nothing similar enough automatically re-run unscoped
  and prefix the reply with a note (`scope_fallback_used: true` on the stored message) — this is the
  three-scenario behavior from the original design (search everything / trust the folder / folder
  turns out empty, so widen automatically).
- `RETRIEVAL_SIMILARITY_THRESHOLD` (cosine distance, lower = more similar) controls the fallback
  trigger. **This is embedding-model- and corpus-dependent** — the default (0.5) was tuned by hand
  against `nomic-embed-text` on a two-document test corpus (recipe vs. printer manual: relevant hits
  landed around 0.2, irrelevant around 0.59). Re-validate it if you switch embedding models or see
  the fallback firing too often/rarely in practice.

### Admin user management

- `keycloak/realm-export.json` also creates `ragchat-backend-admin`, a confidential service-account
  client scoped to the `realm-management` client roles `manage-users`, `view-users`, and
  `view-realm` — deliberately not the Keycloak bootstrap superadmin, so the backend's blast radius
  for user management is limited to this one realm. `app/services/keycloak_admin.py` authenticates
  as this client (client-credentials grant, token cached and auto-refreshed on a 401) to call
  Keycloak's Admin REST API.
- `GET /admin/users` (admin-only) lists every Keycloak user in the realm with their roles and
  whether they've logged into the app at least once (`provisioned`, i.e. have a local `users` row).
- `POST /admin/users` invites a user: creates the Keycloak account with a temporary (must-reset)
  password and the baseline `user` role. The temporary password is returned directly in the
  response for the admin to hand off — there's no email/SMTP integration, which is fine for local
  use but should be replaced with Keycloak's real email flow for anything beyond that.
- `PUT/DELETE /admin/users/{keycloak_id}/roles/{role}` (`admin | user`) grants/revokes a role. An
  admin cannot revoke their own admin role (self-lockout guard).
- JIT provisioning (`app/api/deps.py`) also got hardened this phase: if a Keycloak realm is
  recreated (e.g. `docker volume rm ...keycloak_data` during dev) users get new Keycloak subject
  ids on next login. The old logic would try to `INSERT` a new local user row and hit the unique
  email constraint, throwing a 500. It now reattaches the existing row by email instead.

### Document pipeline

- Embeddings are generated locally via Ollama's `/api/embeddings` endpoint using the
  `nomic-embed-text` model (768 dimensions). Pull it once per fresh `ollama_data` volume:
  `docker compose exec ollama ollama pull nomic-embed-text`
- API flow: `POST /documents` (multipart upload, optional `folder_id` query param) → background
  extraction fills in `GET /documents/{id}/preview` (pages flagged `native` or `ocr_fallback`, with
  a `confidence` score) → `POST /documents/{id}/confirm` chunks + embeds + stores vectors in
  pgvector and marks the document `ingested`.
- Folders: `POST/GET/PATCH/DELETE /folders`. Documents can be filtered by `?folder_id=` or
  `?unfiled=true`, and moved between folders via `PATCH /documents/{id}`.
- PDF pages with fewer than `OCR_FALLBACK_CHAR_THRESHOLD` (default 20) native characters are
  re-extracted via Tesseract OCR — this is what catches scanned/image-only pages.

## Running locally

1. Copy `.env.example` to `.env` and adjust values (at minimum, generate a real
   `SECRET_ENCRYPTION_KEY`; see the comment in `.env.example`).
2. `docker compose up --build`
3. Services:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000 (health check at `/health`)
   - Keycloak admin console: http://localhost:8081
   - Postgres: localhost:5432
   - Ollama: http://localhost:11434

### Keycloak setup (automatic)

The `keycloak` service imports `keycloak/realm-export.json` on first boot (`start-dev --import-realm`),
which creates:

- Realm `ragchat`
- Public client `ragchat-frontend` (used by the SPA's authorization-code + PKCE login flow)
- Bearer-only client `ragchat-backend` (placeholder resource identifier; the backend validates
  tokens by signature/issuer via Keycloak's JWKS endpoint, not by auth'ing as this client)
- Realm roles `user` and `admin`
- Two **dev-only** seed accounts:
  - `testuser` / `testpass` (role: `user`)
  - `admin` / `adminpass` (roles: `admin`, `user`)

Visiting the frontend at http://localhost:5173 redirects to Keycloak's login page; log in with
either seed account. The Keycloak admin console itself remains at http://localhost:8081 (login
`admin`/`admin` unless overridden in `.env`) if you need to inspect or edit the realm directly.

Change or remove the seed accounts before any non-local deployment — they're committed to the repo
in plaintext for local dev convenience only.

The backend authenticates requests by validating the bearer token's signature against Keycloak's
JWKS and checking `iss` against `KEYCLOAK_ISSUER`; on first request from a given Keycloak subject it
transparently creates a local `users` row (JIT provisioning) and keeps its `role` column in sync
with the token's realm roles on every request. Try it once the stack is up:

```
curl http://localhost:8000/me -H "Authorization: Bearer <token from the frontend's network tab>"
```

### Database migrations

Once inside the `backend` container (or with a local Python env pointed at the same `DATABASE_URL`):

```
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```

After pulling code changes, always run `docker compose exec backend alembic upgrade head` — several
migrations since the initial schema (provider credential key hints, message citation snapshots)
need to be applied on any instance that was already running.

## Local development without Docker

- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
  (requires a local Postgres+pgvector instance; set `DATABASE_URL` accordingly)
- Frontend: `cd frontend && npm install && npm run dev`

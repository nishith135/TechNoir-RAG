# TechNoir-RAG — Deployment & Production Checklist

This checklist provides operational requirements for running TechNoir-RAG, covering both the current hosted environment and considerations for the upcoming local-first self-hosted transition.

---

## 1. Secrets & Credentials Management
- [ ] **No Hardcoded Secrets**: Verify that `.env` is absent from source control and `.env.example` contains only dummy placeholders.
- [ ] **Secret Key Strength**: Ensure `SECRET_KEY` is generated via a cryptographically secure random generator (e.g., `openssl rand -hex 32`).
- [ ] **Gemini API Key Protection**: Verify `GEMINI_API_KEY` is loaded strictly via environment variables on the backend and never exposed to Vite frontend bundles or client logs.
- [ ] **Key Rotation**: If a key is ever exposed or compromised, immediately rotate it in the cloud console.

---

## 2. API & Network Security
- [ ] **Production CORS**: Ensure `CORS_ORIGINS` is configured with the exact origin(s) of the frontend (e.g., `https://technoir-rag.onrender.com` or `http://localhost:5173`), avoiding wildcard `*`.
- [ ] **HTTPS / TLS**: Terminate TLS at the reverse proxy (NGINX/Cloudflare/Render) with modern TLS 1.2+ ciphers.
- [ ] **Security Headers**: Verify the presence of `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- [ ] **Rate Limiting**: Apply reverse-proxy or gateway-level rate limiting on `/auth/login` and `/auth/register` to prevent brute force attempts.

---

## 3. Storage & Multi-Tenant Isolation
- [ ] **Path Traversal Protection**: Ensure document retrieval and download routes strictly validate that file paths reside within designated storage roots.
- [ ] **Persistent Volume Mounts**: In Docker or containerized environments, verify that both vector store (`/app/chroma_db`), database (`/app/users.db`), and PDF store (`/app/pdf_store`) are mounted to persistent host volumes.
- [ ] **Exclusion Rules**: Confirm `.gitignore` and `.dockerignore` exclude `.env`, `chroma_db/`, `users.db`, and `pdf_store/`.

---

## 4. File Upload & Ingestion Controls
- [ ] **Maximum Upload Limit**: Enforce a 25MB maximum upload limit at both the reverse proxy (`client_max_body_size`) and application layer.
- [ ] **Magic Byte Verification**: Reject non-PDF files that do not start with `%PDF-` bytes.
- [ ] **Processing Guardrails**: Enforce a maximum page threshold (e.g., 100 pages) to protect against memory exhaustion and excessive API consumption.
- [ ] **Temporary File Cleanup**: Ensure temporary ingestion artifacts are deleted immediately after indexing, and uploaded PDFs are purged if ingestion errors occur.

---

## 5. RAG Pipeline & Prompt Controls
- [ ] **Context Delimiters**: Enforce structural `<context>` XML encapsulation around retrieved document chunks.
- [ ] **Untrusted Data Directive**: Verify system prompts explicitly state that context content is untrusted user data.
- [ ] **Query Length Restrictions**: Constrain user query length to reasonable maximums (<= 2000 characters).

---

## 6. Error Handling & Logging
- [ ] **Exception Masking**: Confirm that production API error responses return generic messages (`"Internal Server Error"`) rather than raw Python stack traces.
- [ ] **Log Scrubbing**: Ensure sensitive user payloads, API keys, and authorization headers are omitted from logs.

---

## 7. Migration Checklist: Local-First / Bring-Your-Own-Key (Next Phase)
When executing the planned transition to a local-first application:
- [ ] **Decommission Hosted Deployment**: Spin down hosted Render services to eliminate continuous cloud API cost exposure.
- [ ] **Local LLM Backend**: Configure pluggable inference providers (e.g., Ollama at `http://localhost:11434`, llama.cpp, or direct user-entered Gemini key).
- [ ] **Local Embeddings**: Add optional local embedding model support (e.g., HuggingFace `all-MiniLM-L6-v2` or Ollama embeddings) so retrieval works 100% offline.
- [ ] **Single-User Architecture**: Simplify or bypass the multi-tenant JWT registration flow for local desktop runs.
- [ ] **One-Command Setup**: Provide a clean `docker compose up` or native local startup script with clear instructions in the rewritten README.

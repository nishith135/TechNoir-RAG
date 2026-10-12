# TechNoir-RAG — Security Remediation Log

This log records security remediations applied to the TechNoir-RAG codebase, their rationale, security impact, and regression validation details.

---

## Log Entries

### REM-01: Multi-Tenant Collision Mitigation (SEC-01)
- **Finding ID**: SEC-01
- **Files Modified**: `backend/main.py`
- **Reason for Change**: Prevent collection name collisions caused by lossy 24-character truncation and character replacement of user email addresses.
- **Remediation Details**:
  - Replaced lossy truncation with deterministic SHA-256 digest scoping (`u_{hash12}__{display_name}`).
  - Constrained collection display name length to ensure full names fit cleanly within ChromaDB's 63-character limit.
- **Security Impact**: Eliminates collection name collisions between different users sharing prefixes.
- **Strategic Direction Note**: Serves as a safe, targeted interim fix without redesigning user tables, as the project is migrating to a single-user local-first architecture.

---

### REM-02: Path Traversal Prevention on Document Routes (SEC-02)
- **Finding ID**: SEC-02
- **Files Modified**: `backend/main.py`
- **Reason for Change**: Prevent directory traversal attacks on `/download/{collection}` and `/document-meta`.
- **Remediation Details**:
  - Added strict input sanitization on collection parameters.
  - Implemented `_safe_resolve_path(base_dir, filename)` verifying that resolved paths are strictly children of `PDF_STORE_PATH` or `CHROMA_PERSIST_PATH` using `resolve().is_relative_to(base)`.
  - Rejects any traversal attempt with HTTP 400 or HTTP 404.
- **Security Impact**: Guarantees that neither hosted attackers nor local malicious files can read arbitrary files outside the designated storage folder.
- **Validation**: Tested with `../` and path traversal patterns; safely rejected.

---

### REM-03: Upload Safety, Magic Bytes & Ingestion Resource Controls (SEC-03)
- **Finding ID**: SEC-03
- **Files Modified**: `backend/main.py`, `backend/ingest.py`
- **Reason for Change**: Prevent memory exhaustion (OOM), unhandled file types, and disk leaks.
- **Remediation Details**:
  - Replaced unbounded `await file.read()` with chunked streaming reader enforcing a strict 25 MB limit (`MAX_UPLOAD_BYTES`), returning HTTP 413 if exceeded.
  - Added magic byte validation verifying that uploaded files begin with `%PDF-` signature.
  - Added a maximum page limit (`MAX_PAGES = 100`) in `backend/ingest.py` to prevent runaway processing on enormous documents.
  - Added cleanup logic in `upload_pdf` exception handling to ensure any partially written files in `pdf_store/` or `tmp/` are removed if ingestion fails.
- **Security Impact**: Shields the backend from memory denial of service and orphaned disk bloat.
- **Validation**: Verified with mock oversized payloads and non-PDF byte streams.

---

### REM-04: Error Response Masking & Information Disclosure Prevention (SEC-04)
- **Finding ID**: SEC-04
- **Files Modified**: `backend/main.py`
- **Reason for Change**: Prevent leakage of internal file paths, database schemas, and stack traces in API responses.
- **Remediation Details**:
  - Updated `global_exception_handler` to return a generic `"Internal Server Error"` message while logging detailed diagnostics to internal logs.
  - Replaced raw exception string propagation in `/upload`, `/query`, `/chunks`, and `/document-meta` with generic client errors.
- **Security Impact**: Protects internal server implementation details from unauthorized disclosure.

---

### REM-05: CORS Configuration & Security Headers (SEC-05, SEC-08)
- **Finding ID**: SEC-05, SEC-08
- **Files Modified**: `backend/config.py`, `backend/main.py`, `frontend/nginx.conf`
- **Reason for Change**: Ensure CORS is loaded from environment settings rather than wildcards; supply defense-in-depth HTTP headers.
- **Remediation Details**:
  - Added `CORS_ORIGINS` parsing in `backend/config.py` from comma-separated environment variables.
  - Added middleware setting `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin`.
  - Added matching headers to `frontend/nginx.conf`.
- **Security Impact**: Enforces origin restrictions and browser MIME/clickjacking protections.

---

### REM-06: RAG Prompt Boundary Delimitation & Input Validation (SEC-06)
- **Finding ID**: SEC-06
- **Files Modified**: `backend/prompts.py`, `backend/main.py`
- **Reason for Change**: Fortify the RAG pipeline against prompt injection via adversarial document content.
- **Remediation Details**:
  - Enclosed retrieved chunks within explicit `<context>` and `<document_chunk>` XML tags in `backend/prompts.py`.
  - Added system instructions explicitly directing the model to treat content within `<context>` as passive evidence, never as executable instructions.
  - Constrained query length in `QueryRequest` (1 to 2000 characters) and retrieval parameter `k` (1 to 20).
- **Security Impact**: Reduces prompt injection risks and prevents unbounded prompt payloads.

---

### REM-07: Storage Persistence & Git Exclusion Hardening (SEC-09, SEC-10)
- **Finding ID**: SEC-09, SEC-10
- **Files Modified**: `.gitignore`, `.dockerignore`, `docker-compose.yml`, `backend/ingest.py`
- **Reason for Change**: Prevent accidental tracking of uploaded PDFs in Git or Docker images; fix metadata path resolution.
- **Remediation Details**:
  - Added `pdf_store/` to `.gitignore` and `.dockerignore`.
  - Added `./pdf_store:/app/pdf_store` volume mapping in `docker-compose.yml`.
  - Fixed `backend/ingest.py` to write metadata directly into `Path(CHROMA_PERSIST_PATH) / f"{collection_name}_meta.json"`.
- **Security Impact**: Guarantees data persistence across container restarts while preventing sensitive PDF documents from leaking into build artifacts.

---

## Automated Validation Results

All 14 backend regression and security unit tests executed and passed on October 13, 2026:

```
Ran 14 tests in 12.149s

OK

Test Breakdown:
[PASS] test_health (test_api.TestAPI.test_health)
[PASS] test_login_invalid_credentials (test_api.TestAPI.test_login_invalid_credentials)
[PASS] test_root (test_api.TestAPI.test_root)
[PASS] test_unauthenticated_collections (test_api.TestAPI.test_unauthenticated_collections)
[PASS] test_unauthenticated_me (test_api.TestAPI.test_unauthenticated_me)
[PASS] test_version (test_api.TestAPI.test_version)
[PASS] test_download_path_traversal_rejected (test_security.SecurityTestSuite)
[PASS] test_email_validation (test_security.SecurityTestSuite)
[PASS] test_error_masking (test_security.SecurityTestSuite)
[PASS] test_path_traversal_safe_resolver (test_security.SecurityTestSuite)
[PASS] test_prompt_injection_boundary_encapsulation (test_security.SecurityTestSuite)
[PASS] test_security_headers_present (test_security.SecurityTestSuite)
[PASS] test_upload_magic_bytes_validation (test_security.SecurityTestSuite)
[PASS] test_user_prefix_collision_prevention (test_security.SecurityTestSuite)
```

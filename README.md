# 🧠 TechNoir-RAG: Local-First Private Document Intelligence

TechNoir-RAG is a self-hosted, local-first Retrieval-Augmented Generation (RAG) system engineered for private, offline document analysis. Run powerful local LLMs and embeddings directly on your own computer with **zero API costs, zero data egress, and zero cloud lock-in**.

Pairing a high-performance **FastAPI** backend with an immersive, cyberpunk-inspired **React** interface, TechNoir-RAG delivers split-pane PDF inspection, interactive source citations, and a tri-stage hybrid retrieval pipeline.

---

## ⚡ Why Local-First?

- 💸 **Zero API Cost**: No token fees, surprise cloud invoices, or subscription quotas. Powered by local models running on your machine via [Ollama](https://ollama.com/).
- 🔒 **100% Private & Confidential**: Your proprietary PDFs and research never leave your hardware. No third-party servers see your data.
- 🔀 **Decoupled Providers**: Independently configure your LLM generation (`LLM_PROVIDER`) and embedding model (`EMBEDDING_PROVIDER`). Use Ollama offline, or plug in your own Google Gemini key whenever you choose.
- 🎯 **Deep Context Verification**: Interactive citations map generative answers back to specific PDF pages with Euclidean/cosine similarity confidence scores.

---

## ✨ Features & Architecture

### 1. Tri-Stage Hybrid Retrieval Pipeline
- **Dense Vector Search**: ChromaDB semantic matching across document chunks.
- **Lexical BM25 Search**: Exact keyword indexing for domain-specific acronyms and proper nouns.
- **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse candidates into a balanced pool.
- **Cross-Encoder Reranking**: Re-scores candidates using local NLP cross-encoders (`ms-marco-MiniLM-L-6-v2`) before generating the final answer.

### 2. Immersive "Tech Noir" Split-Pane Workspace
- **Dual-Pane Interface**: Read original PDFs in the embedded viewer alongside the AI assistant.
- **Live Source Citations**: Hover over citations in responses to preview source pages and vector distances.
- **Chunk Explorer**: Inspect indexed raw chunks and document metadata.
- **Telemetry Dashboard**: Monitor ingestion statistics, collections, and pipeline metrics.

### 3. Hardened Security
Audited and hardened against application security vulnerabilities (see [audit/security-audit.md](file:///c:/Projects/TechNoir-RAG/audit/security-audit.md)):
- Strict path traversal defenses on document downloads and metadata resolution.
- Magic byte (`%PDF-`) validation and streaming upload size limits (25 MB).
- Prompt boundary protection isolating untrusted document context with XML delimiter tags.
- Deterministic collection isolation and generic error masking.

---

## 🚀 Quickstart (3 Steps)

### Step 1: Install Ollama & Pull Models
Install [Ollama](https://ollama.com/) on your computer, then pull your preferred LLM and embedding model:
```bash
# Recommended models (fast, accurate, lightweight)
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Step 2: Configure Environment
Clone the repository and copy the example environment file:
```bash
git clone https://github.com/your-org/TechNoir-RAG.git
cd TechNoir-RAG
cp .env.example .env
```
The default `.env` is pre-configured for local Ollama use:
```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
LOCAL_MODE=true
```

### Step 3: Run the Application

#### Option A: Docker Compose (Recommended)
```bash
docker compose up --build
```
- Open **http://localhost** in your browser.
- The backend API is available at **http://localhost:8000** (Swagger docs at `/docs`).

#### Option B: Native Run (Python + Node.js)
**Backend:**
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Navigate to **http://localhost:5173**.

---

## ⚙️ Configuration & Providers

TechNoir-RAG decouples model generation and embeddings. You can configure them independently in `.env`:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Provider for answer generation: `ollama` or `gemini` |
| `EMBEDDING_PROVIDER` | `ollama` | Provider for vector embeddings: `ollama` or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint (`http://host.docker.internal:11434` in Docker) |
| `OLLAMA_MODEL` | `llama3.2` | Local model tag (e.g. `llama3.2`, `mistral`, `deepseek-r1`) |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model tag (e.g. `nomic-embed-text`, `all-minilm`) |
| `LOCAL_MODE` | `true` | Enables local development fallbacks and single-user optimizations |
| `AUTH_OPTIONAL` | `false` | Set to `true` to disable login prompts for single-user desktop convenience |
| `GEMINI_API_KEY` | *(empty)* | Optional: Google Gemini API key if using cloud provider |
| `MAX_UPLOAD_BYTES` | `26214400` | Maximum upload size (default: 25 MB) |
| `MAX_INGEST_PAGES` | `100` | Maximum PDF pages ingested per document |

---

## 🔒 Cloud Decommissioning & Cost Elimination

If you previously deployed TechNoir-RAG to hosted cloud providers (such as Render, Vercel, or Railway) and wish to eliminate API and hosting costs:

1. **Spin Down Hosted Services**:
   - Log into your Render / Cloud dashboard.
   - Delete or suspend the Web Service instances running the frontend and backend.
2. **Revoke Cloud API Keys**:
   - Go to Google AI Studio or your cloud provider dashboard.
   - Delete or revoke any API keys previously provisioned for the hosted app to ensure no unexpected billing occurs.
3. **Migrate Local Data (Optional)**:
   - If you have existing collections on a hosted instance, copy `users.db` and the `chroma_db/` folder to your local machine.
4. **Run 100% Free Locally**:
   - By following the Quickstart above with Ollama, your application operates entirely on your local machine with zero recurring expense.

---

## 🧪 Testing

Run the automated test suite (including API regression tests, security verification, and provider decoupling):
```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

---

## 📜 License

MIT License. Built for private, open, and accessible document intelligence.

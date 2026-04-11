# 🧠 Tech Noir RAG: Premium AI Document Analysis Framework

Tech Noir RAG is a comprehensive, full-stack Retrieval-Augmented Generation system designed for multi-tenant, secure, and blazingly fast document analysis. Built entirely from the ground up, this modern infrastructure bridges a heavy-duty FastAPI backbone with a beautifully designed, immersive "Tech Noir" styled React interface.

Powered by Google's Gemini API, advanced hybrid vector search, and cross-encoder reranking, the platform intelligently contextualizes enterprise documents (PDFs) to deliver highly accurate, hallucination-free generative answers.

---

## ✨ System Highlights

### 1. The "Tech Noir" User Interface
- **Premium Aesthetics**: Fully bespoke UI leveraging a sleek, dark-mode Tech Noir color scheme with vibrant dynamic interactions.
- **Split-Pane Analysis Workspace**: Allows users to view their active PDF document side-by-side with an interactive, context-aware chatbot.
- **Dynamic Citation System**: The LLM automatically cites its sources. The UI parses these into interactive links that, when hovered, display the exact source page and Euclidean/cosine distance confidence score of the extracted text.
- **Interactive Analytics Dashboard**: Beautifully visualizes total ingested documents, active collections, pipeline stages, and system metrics.

### 2. Multi-Tenant Enterprise Security
- **Per-User Isolation**: Engineered with full multi-tenant architecture. Every file uploaded is securely hashed and namespaced to the unique authenticated user. Users absolutely cannot query, view, or access documents outside their strict namespace.
- **JWT & Persistent Auth**: Complete login and registration flows powered by bcrypt hashing and secure JWT tokens scoped to local sessions.

### 3. Advanced Tri-Stage Retrieval Pipeline
Tech Noir RAG doesn't just do basic vector search. It implements a state-of-the-art hybrid pipeline to defeat the edge cases of simple RAG:
1. **Dense Semantic Search**: Gemini-accelerated embeddings (`models/gemini-embedding-001`) map textual concepts into 3072-dimensional space, capturing high-level meaning and semantic intent.
2. **Lexical BM25 Search**: Traditional keyword-based retrieval algorithm runs simultaneously to strictly match niche terminology, acronyms, and proper nouns that vectors often miss.
3. **Reciprocal Rank Fusion (RRF)**: A specialized algorithm statistically merges the dense and lexical results to create a balanced, hyper-accurate candidate pool.
4. **Cross-Encoder Reranking**: The candidates are piped into a localized NLP model (`ms-marco-MiniLM-L-6-v2`) which reads both the *query* and the *extracted text* side-by-side to score their true pairwise relevance before finally passing the absolute best context to the LLM.

### 4. Robust Document Ingestion
- **Automated Text Chunking**: High-fidelity PDF processing uses `pdfplumber` to accurately read complex layouts, intelligently chunking text at 800-character limits with contextual overlaps.
- **Batched Processing**: Automatically batches embedding tasks to safely distribute payload weight when indexing massive corporate documents.

---

## 🏗️ Technology Stack

**Frontend Framework**
- React 18 & Vite
- Tailwind CSS (Custom Design System & Variables)
- Context API (Auth State Management)

**Backend Architecture**
- FastAPI (Python 3.11 asynchronous web server)
- SQLite (Auth Storage via WAL mode for high concurrency)
- ChromaDB (Persistent Vector Database)
- Google GenAI SDK (LLM Generation & Embedding)
- Sentence-Transformers (Cross-Encoder inference)

**Deployment / DevOps**
- Docker & Docker Compose
- NGINX Proxy (Configured with high-duration timeouts and 50M payload caps)

---

## 🚀 Deployment & Installation

### Prerequisites
- Node.js (v20+)
- Python (3.11+)
- Docker (Optional but recommended)
- **Google Gemini API Key** (Retrieve from Google AI Studio)

### 1. Environment Setup
Clone the repository and copy the environment template:
```bash
git clone https://github.com/your-org/TechNoir-RAG.git
cd TechNoir-RAG
cp .env.example .env
```
Update your `.env` with a secure random string and your Gemini Key:
```env
SECRET_KEY=your_super_secret_jwt_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
EMBED_MODEL=models/gemini-embedding-001
CORS_ORIGINS=http://localhost:5173,http://localhost:8000,http://localhost
```

### Option A: Fully Containerized via Docker (Production / Quickstart)
The entire platform is configured to spin up securely inside interdependent containers.

```bash
docker-compose up --build
```
- Access the web interface at: `http://localhost`
- Access the backend API directly at: `http://localhost:8000`

### Option B: Local Engineering Mode (Development)
If you wish to modify the application, run it natively.

**Backend Startup:**
```bash
python -m venv backend/venv
source backend/venv/bin/activate  # Windows: backend\venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```
**Frontend Startup:**
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`. *(The Vite configuration automatically proxies backend networking across localhost directly to the Uvicorn loopback).*

---

## 📖 API Documentation

FastAPI automatically generates interactive Swagger documentation. When the system is running, visit **`http://localhost:8000/docs`**.

### Core Secured Endpoints
| HTTP | Endpoint | Action |
|---|---|---|
| `POST` | `/auth/register` | Mint a new user account (Requires Email & Password). |
| `POST` | `/auth/login` | Authenticate and retrieve an active JWT Bearer token. |
| `POST` | `/upload` | Accept `.pdf` form-data. Chunks, embeds, and scopes the document to the active user's internal ChromaDB namespace. |
| `POST` | `/query` | Execute the hybrid search pipeline against a target collection and stream a generated LLM answer. |
| `GET` | `/collections` | Pull a strictly sanitized array of the authenticated user's uploaded active document scopes. |

---

## 🛡️ Best Practices & Known Limitations
- **Ingestion Quotas**: The system relies on Google's Embedding API limit structure. If you intend to upload textbooks or massive databases (1000+ pages), ensure you upgrade your Google API tier to prevent rate-limit throttling.
- **Security Check**: Your `users.db` and `chroma_db` directories will store persistent, localized data. In a production cloud push, bind these directories to remote storage volumes, and **never push `.env` to GitHub.**

## 🤝 Contributing
Contributions are heavily encouraged to map out future models (such as integrating local DeepSeek/Llama fallback routines) and expand the frontend telemetry. Open a GitHub Issue for large-scale systemic changes before proposing PRs.

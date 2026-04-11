# Tech Noir RAG 🧠 

A state-of-the-art Retrieval-Augmented Generation (RAG) system built with FastAPI, React, and Google's Gemini API. This application allows users to securely upload PDF documents to their own isolated workspace, index the content into a vector database, and chat with a powerful LLM to extract information, summarize concepts, and analyze the text.

![Tech Noir RAG](frontend/public/vite.svg) *Replace with a screenshot of the UI*

## ✨ Features

- **Google Gemini Integration**: Utilizes `gemini-2.5-flash` for high-quality, lightning-fast text generation and conversational reasoning.
- **Advanced Hybrid Retrieval Pipeline**: 
  - **Dense Semantic Search**: High-dimensional vector embeddings using Gemini (`models/gemini-embedding-001`).
  - **Lexical Search (BM25)**: Keyword-based matching to capture exact terminology.
  - **Reciprocal Rank Fusion (RRF)**: Combines and balances the results of Dense and Lexical retrieval.
  - **Cross-Encoder Reranking**: Uses `ms-marco-MiniLM-L-6-v2` to intelligently re-score and surface the most contextually relevant chunks.
- **Per-User Isolation**: Multi-tenant architecture. User accounts are isolated; documents uploaded by one user are strictly sandboxed and invisible to others.
- **JWT Authentication**: Secure user registration and login workflows using bcrypt and JWTs.
- **FastAPI Backend**: Asynchronous, highly scalable REST API.
- **React + Vite Frontend**: Beautiful, modern UI built with React and Tailwind CSS.
- **Docker Ready**: Fully containerized backend and frontend (backed by NGINX) for instant deployment.

## 🏗️ Architecture

- **Frontend**: React.js, Vite, Tailwind CSS.
- **Backend Framework**: FastAPI (Python 3.11).
- **Vector Database**: ChromaDB (Persistent local storage).
- **Relational Database**: SQLite (User management via WAL mode).
- **LLM & Embeddings**: Google Gemini API (`google-generativeai`).
- **PDF Processing**: `pdfplumber` for robust text extraction.
- **Proxy/Web Server**: NGINX (Configured for large PDF uploads and timeout management).

## 🚀 Getting Started

### Prerequisites
- Node.js (v20+)
- Python (3.11+)
- Docker & Docker Compose (Optional, for containerized run)
- A **Google Gemini API Key** (Get one from Google AI Studio)

### 1. Environment Configuration

Clone the repository and create a `.env` file in the root directory:

```bash
git clone https://github.com/nishith135/TechNoir-RAG.git
cd TechNoir-RAG
cp .env.example .env
```

Edit your `.env` file and add your credentials:
```env
SECRET_KEY=your_super_secret_jwt_key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMBED_MODEL=models/gemini-embedding-001
CORS_ORIGINS=http://localhost:5173,http://localhost:8000,http://localhost
```

---

### Option A: Run with Docker Compose (Recommended)

To spin up the entire stack seamlessly:

```bash
docker-compose up --build
```
- The Frontend will be available at: http://localhost
- The Backend API will be available at: http://localhost:8000
- Swagger API Docs will be available at: http://localhost:8000/docs

---

### Option B: Run Locally (Dev Mode)

#### 1. Start the Backend

```bash
# Create and activate a virtual environment
python -m venv backend/venv
source backend/venv/bin/activate  # On Windows: backend\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn backend.main:app --reload --port 8000
```

#### 2. Start the Frontend

In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`. 

*(Note for Windows users: `vite.config.js` is set to proxy API requests to `127.0.0.1:8000` to avoid Docker localhost hijacking).*

## 📖 API Documentation

Once the backend is running, navigate to `http://localhost:8000/docs` to interact with the OpenAPI/Swagger documentation.

### Core Endpoints

| URL | Method | Description |
|---|---|---|
| `/auth/register` | `POST` | Create a new user account. |
| `/auth/login`    | `POST` | Authenticate and receive a JWT. |
| `/auth/me`       | `GET`  | Get the current authenticated user's profile. |
| `/upload`        | `POST` | Upload a PDF document. Returns ingestion stats. Requires JWT. |
| `/query`         | `POST` | Ask a question against an ingested document collection. Requires JWT. |
| `/collections`   | `GET`  | List all document collections belonging to the current user. Requires JWT. |

## 🛡️ Security Notes
- **Never commit your `.env` or `users.db` to version control.**
- Ensure `SECRET_KEY` is completely randomized in a production environment.
- The `gemini-2.5-flash` model performs optimally with current rate limits. If you plan to ingest massive PDFs concurrently, consider monitoring your Gemini API quota.

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

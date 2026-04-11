import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import LoginPage from "./LoginPage";
import RegisterPage from "./RegisterPage";

/* ─── Spinner ─── */
function Spinner({ size = 16 }) {
  return (
    <span
      className="inline-block animate-spin rounded-full border-2 border-outline-variant border-t-primary"
      style={{ width: size, height: size }}
      aria-label="loading"
    />
  );
}

/* ─── Citation Button ─── */
function CitationPill({ page, distance, isOpen, onClick }) {
  return (
    <div className="relative inline-flex">
      <button
        type="button"
        onClick={onClick}
        className="ml-2 inline-flex items-center gap-1 bg-surface-container-highest px-2 py-0.5 rounded text-[10px] font-bold text-primary hover:text-white transition-colors"
      >
        <span className="material-symbols-outlined text-[12px]">link</span>
        P.{page}
      </button>
      {isOpen && (
        <div className="absolute left-1/2 top-full z-10 -translate-x-1/2 mt-2 w-52 rounded-lg border border-outline-variant bg-surface-container-high p-3 text-xs shadow-2xl animate-fade-in-up">
          <div className="font-bold text-on-surface uppercase tracking-widest text-[10px]">
            Source Details
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-on-surface-variant">Page</span>
            <span className="text-on-surface font-mono">{page}</span>
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-on-surface-variant">Distance</span>
            <span className="text-on-surface font-mono">
              {Number(distance).toFixed(4)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Settings Panel ─── */
function SettingsPanel({ onClose, user, onLogout }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-surface-container border border-outline-variant/20 rounded-xl w-full max-w-lg p-8 shadow-2xl animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-headline font-bold text-on-surface">
            Settings
          </h2>
          <button
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* User Profile Section */}
        <div className="mb-6 p-4 bg-surface-container-high rounded-lg">
          <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-3">
            Account
          </div>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary-container text-2xl">
                person
              </span>
            </div>
            <div>
              <div className="text-on-surface font-medium">
                {user?.username || "User"}
              </div>
              <div className="text-sm text-on-surface-variant">
                {user?.email || ""}
              </div>
            </div>
          </div>
        </div>

        {/* Model Config */}
        <div className="mb-6 p-4 bg-surface-container-high rounded-lg">
          <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-3">
            AI Configuration
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">
                Chat Model
              </span>
              <span className="text-sm text-on-surface font-mono bg-surface-container-lowest px-3 py-1 rounded">
                Gemini 1.5 Flash
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">
                Embedding Model
              </span>
              <span className="text-sm text-on-surface font-mono bg-surface-container-lowest px-3 py-1 rounded">
                gemini-embedding-001
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">
                Chunk Size
              </span>
              <span className="text-sm text-on-surface font-mono bg-surface-container-lowest px-3 py-1 rounded">
                800 chars
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">
                Retrieval Top-K
              </span>
              <span className="text-sm text-on-surface font-mono bg-surface-container-lowest px-3 py-1 rounded">
                5 chunks
              </span>
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="mb-6 p-4 bg-surface-container-high rounded-lg">
          <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-3">
            System
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">Version</span>
              <span className="text-sm text-on-surface">AI Engine v2.4</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-on-surface-variant">Retrieval</span>
              <span className="text-sm text-on-surface">
                Hybrid (Semantic + BM25 + Rerank)
              </span>
            </div>
          </div>
        </div>

        {/* Logout */}
        <button
          id="logout-button"
          onClick={onLogout}
          className="w-full border border-error/30 text-error py-3 rounded-lg text-sm font-bold uppercase tracking-widest hover:bg-error/10 transition-all flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-base">logout</span>
          Sign Out
        </button>
      </div>
    </div>
  );
}

/* ─── Nav Items ─── */
const NAV_ITEMS = [
  { icon: "description", label: "Documents", id: "documents" },
  { icon: "chat_bubble", label: "Chat", id: "chat" },
  { icon: "analytics", label: "Analytics", id: "analytics" },
  { icon: "settings", label: "Settings", id: "settings" },
];

/* ─── Main App ─── */
export default function App() {
  const { user, loading: authLoading, logout, authFetch } = useAuth();
  const [authPage, setAuthPage] = useState("login"); // "login" | "register"

  // ── If auth is still loading, show spinner ──
  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner size={32} />
      </div>
    );
  }

  // ── If not logged in, show login/register ──
  if (!user) {
    if (authPage === "register") {
      return <RegisterPage onSwitchToLogin={() => setAuthPage("login")} />;
    }
    return <LoginPage onSwitchToRegister={() => setAuthPage("register")} />;
  }

  // ── Authenticated: show main app ──
  return <MainApp user={user} logout={logout} authFetch={authFetch} />;
}

/* ═══════════════════════════════════════════════════════════════
   Main authenticated application
   ═══════════════════════════════════════════════════════════════ */
function MainApp({ user, logout, authFetch }) {
  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  const [collections, setCollections] = useState([]);
  const [activeCollection, setActiveCollection] = useState("");

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [openCitationIndex, setOpenCitationIndex] = useState(null);
  const [activeNav, setActiveNav] = useState("chat");
  const [showSettings, setShowSettings] = useState(false);

  const activeSourcesByMessageId = useMemo(() => {
    const map = new Map();
    for (const msg of messages) {
      if (msg.role === "bot" && Array.isArray(msg.sources)) {
        map.set(msg.id, msg.sources);
      }
    }
    return map;
  }, [messages]);

  async function fetchCollections() {
    const res = await authFetch("/collections");
    if (!res.ok) throw new Error("Failed to load collections.");
    const data = await res.json();
    return data.collections || [];
  }

  useEffect(() => {
    fetchCollections()
      .then((cols) => {
        setCollections(cols);
        if (cols.length) setActiveCollection((prev) => prev || cols[0]);
      })
      .catch(() => {
        setCollections([]);
      });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  async function handleUploadClick() {
    setUploadError("");
    if (fileInputRef.current) fileInputRef.current.click();
  }

  async function handleUploadFile(file) {
    if (!file) return;
    setUploading(true);
    setUploadError("");
    setOpenCitationIndex(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await authFetch("/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || "Upload failed.");
      }

      const summary = await res.json();

      const cols = await fetchCollections();
      setCollections(cols);
      if (summary?.collection) setActiveCollection(summary.collection);
      else if (cols.length) setActiveCollection(cols[0]);

      // Switch to chat view after successful upload
      setActiveNav("chat");
    } catch (e) {
      setUploadError(e?.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSend() {
    const trimmed = question.trim();
    if (!trimmed || chatLoading) return;
    if (!activeCollection) return;

    setChatLoading(true);
    setOpenCitationIndex(null);

    const userMsg = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");

    try {
      const res = await authFetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          collection: activeCollection,
          k: 5,
        }),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || "Query failed.");
      }

      const data = await res.json();

      const botMsg = {
        id: crypto.randomUUID(),
        role: "bot",
        content: data.answer || "",
        sources: data.sources || [],
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      const botMsg = {
        id: crypto.randomUUID(),
        role: "bot",
        content: e?.message || "Something went wrong.",
        sources: [],
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setChatLoading(false);
    }
  }

  const [dragOver, setDragOver] = useState(false);

  const suggestions = [
    "What are the key findings in the report?",
    "Summarize the main concepts",
    "Explain the technical implementation",
  ];

  const currentTime = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  // Handle sidebar nav clicks
  function handleNavClick(id) {
    if (id === "settings") {
      setShowSettings(true);
    } else {
      setActiveNav(id);
    }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-on-surface font-body">
      {/* ═══════ TOP APP BAR ═══════ */}
      <header className="flex justify-between items-center px-6 h-16 w-full z-50 font-headline text-sm tracking-tight bg-surface-container-low border-b border-outline-variant/10">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-primary">
            Tech Noir RAG
          </span>
          <nav className="hidden md:flex gap-6">
            <a
              className={
                "cursor-pointer transition-colors duration-200 " +
                (activeNav !== "settings"
                  ? "text-primary border-b border-primary"
                  : "text-on-surface-variant hover:text-white")
              }
              onClick={() => setActiveNav("chat")}
            >
              Projects
            </a>
            <a
              className={
                "cursor-pointer transition-colors duration-200 " +
                (activeNav === "documents"
                  ? "text-primary border-b border-primary"
                  : "text-on-surface-variant hover:text-white")
              }
              onClick={() => setActiveNav("documents")}
            >
              Knowledge Base
            </a>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button className="text-on-surface-variant hover:text-white transition-colors duration-200">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="text-on-surface-variant hover:text-white transition-colors duration-200"
          >
            <span className="material-symbols-outlined">settings</span>
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden border border-outline-variant bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary-container text-sm">
                person
              </span>
            </div>
            <span className="hidden md:inline text-xs text-on-surface-variant group-hover:text-on-surface transition-colors">
              {user?.username}
            </span>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ═══════ SIDE NAV BAR ═══════ */}
        <aside className="hidden md:flex flex-col h-full w-64 py-8 px-4 font-label text-xs font-bold uppercase tracking-widest bg-background border-r border-outline-variant/10">
          <div className="mb-8 px-2">
            <h2 className="text-primary font-headline text-lg normal-case tracking-normal">
              Research Suite
            </h2>
            <p className="text-on-surface-variant text-[10px] tracking-widest mt-1">
              AI Engine v2.4
            </p>
          </div>

          <nav className="flex-1 space-y-2">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.id}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavClick(item.id);
                }}
                className={
                  "flex items-center gap-3 px-3 py-3 transition-all rounded " +
                  (activeNav === item.id ||
                  (item.id === "settings" && showSettings)
                    ? "text-primary bg-surface-container-high border-l-2 border-secondary"
                    : "text-on-surface-variant hover:bg-surface-container-high hover:text-white")
                }
              >
                <span className="material-symbols-outlined text-lg">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </a>
            ))}
          </nav>

          {/* New Analysis / Upload Button */}
          <button
            onClick={handleUploadClick}
            className="mt-auto bg-gradient-to-br from-primary to-primary-dim text-on-primary-container py-3 rounded-md font-headline font-bold normal-case tracking-normal hover:opacity-90 transition-opacity"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <Spinner size={16} /> Uploading…
              </span>
            ) : (
              "New Analysis"
            )}
          </button>
        </aside>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleUploadFile(e.target.files?.[0])}
        />

        {/* ═══════ MAIN WORKSPACE ═══════ */}
        <main className="flex-1 flex flex-col md:flex-row overflow-hidden bg-surface">
          {/* ─────── DOCUMENTS VIEW ─────── */}
          {activeNav === "documents" && (
            <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
              <div className="max-w-3xl mx-auto">
                <h2 className="text-2xl font-headline font-bold text-on-surface mb-2">
                  Knowledge Base
                </h2>
                <p className="text-on-surface-variant text-sm mb-8">
                  Manage your indexed documents
                </p>

                {/* Upload Zone */}
                <div
                  onClick={handleUploadClick}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    const file = e.dataTransfer.files?.[0];
                    if (file) handleUploadFile(file);
                  }}
                  className={
                    "flex cursor-pointer flex-col items-center gap-6 rounded-xl border-2 border-dashed p-12 transition-all mb-8 " +
                    (dragOver
                      ? "border-primary bg-primary/5 scale-[1.01]"
                      : "border-outline-variant/40 hover:border-primary/40 hover:bg-surface-container")
                  }
                >
                  {uploading ? (
                    <Spinner size={40} />
                  ) : (
                    <div className="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center">
                      <span
                        className="material-symbols-outlined text-3xl text-primary"
                        style={{
                          fontVariationSettings: "'FILL' 0, 'wght' 300",
                        }}
                      >
                        cloud_upload
                      </span>
                    </div>
                  )}
                  <div className="text-center">
                    <div className="text-lg font-headline font-semibold text-on-surface">
                      Upload Document
                    </div>
                    <div className="mt-2 text-sm text-on-surface-variant">
                      Drag & drop a PDF or click to browse
                    </div>
                  </div>
                </div>

                {uploadError && (
                  <div className="text-sm text-error bg-error-container/20 px-4 py-2 rounded-lg mb-6">
                    {uploadError}
                  </div>
                )}

                {/* Document List */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                    Indexed Documents
                  </span>
                  <span className="bg-secondary-container px-2 py-0.5 rounded text-[10px] font-bold text-on-secondary-container">
                    {collections.length}
                  </span>
                </div>

                {collections.length === 0 ? (
                  <div className="text-center py-16 text-on-surface-variant">
                    <span
                      className="material-symbols-outlined text-5xl mb-4 block opacity-30"
                      style={{ fontVariationSettings: "'FILL' 0, 'wght' 200" }}
                    >
                      folder_open
                    </span>
                    <p className="text-sm">No documents indexed yet</p>
                    <p className="text-xs text-outline mt-1">
                      Upload PDFs to get started
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {collections.map((name) => (
                      <div
                        key={name}
                        className={
                          "flex items-center justify-between p-4 rounded-lg transition-all cursor-pointer " +
                          (name === activeCollection
                            ? "bg-surface-container-high border-l-2 border-secondary"
                            : "bg-surface-container hover:bg-surface-container-high")
                        }
                        onClick={() => {
                          setActiveCollection(name);
                          setActiveNav("chat");
                          setOpenCitationIndex(null);
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-primary">
                            description
                          </span>
                          <div>
                            <div className="text-sm font-medium text-on-surface">
                              {name}
                            </div>
                            <div className="text-[10px] text-on-surface-variant uppercase tracking-widest">
                              PDF Document
                            </div>
                          </div>
                        </div>
                        <button
                          className="text-xs text-primary hover:text-white transition-colors flex items-center gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveCollection(name);
                            setActiveNav("chat");
                          }}
                        >
                          <span className="material-symbols-outlined text-sm">
                            chat
                          </span>
                          Chat
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ─────── ANALYTICS VIEW ─────── */}
          {activeNav === "analytics" && (
            <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
              <div className="max-w-3xl mx-auto">
                <h2 className="text-2xl font-headline font-bold text-on-surface mb-2">
                  Analytics
                </h2>
                <p className="text-on-surface-variant text-sm mb-8">
                  RAG system performance metrics
                </p>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="bg-surface-container p-6 rounded-xl border border-outline-variant/10">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Documents
                    </div>
                    <div className="text-3xl font-headline font-bold text-primary">
                      {collections.length}
                    </div>
                    <div className="text-xs text-on-surface-variant mt-1">
                      Indexed collections
                    </div>
                  </div>
                  <div className="bg-surface-container p-6 rounded-xl border border-outline-variant/10">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Messages
                    </div>
                    <div className="text-3xl font-headline font-bold text-secondary">
                      {messages.length}
                    </div>
                    <div className="text-xs text-on-surface-variant mt-1">
                      This session
                    </div>
                  </div>
                  <div className="bg-surface-container p-6 rounded-xl border border-outline-variant/10">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Retrieval
                    </div>
                    <div className="text-3xl font-headline font-bold text-tertiary">
                      Hybrid
                    </div>
                    <div className="text-xs text-on-surface-variant mt-1">
                      Semantic + BM25 + Rerank
                    </div>
                  </div>
                </div>

                {/* Pipeline Visualization */}
                <div className="bg-surface-container p-6 rounded-xl border border-outline-variant/10 mb-6">
                  <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-4">
                    RAG Pipeline
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    {[
                      "PDF Upload",
                      "Text Extraction",
                      "Chunking",
                      "Embedding",
                      "Vector Store",
                      "Hybrid Retrieval",
                      "Reranking",
                      "LLM Generation",
                    ].map((step, i) => (
                      <div key={step} className="flex items-center gap-3">
                        <div className="bg-surface-container-high px-3 py-2 rounded-lg text-xs text-on-surface">
                          {step}
                        </div>
                        {i < 7 && (
                          <span className="material-symbols-outlined text-sm text-outline">
                            arrow_forward
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Active Collection Info */}
                {activeCollection && (
                  <div className="bg-surface-container p-6 rounded-xl border border-outline-variant/10">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-3">
                      Active Context
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-primary">
                        description
                      </span>
                      <div>
                        <div className="text-sm font-medium text-on-surface">
                          {activeCollection}
                        </div>
                        <div className="text-xs text-on-surface-variant">
                          Currently selected for queries
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ─────── CHAT VIEW (split layout) ─────── */}
          {activeNav === "chat" && (
            <>
              {/* ── LEFT: Document Viewer ── */}
              <section className="flex-[1.2] flex flex-col bg-surface-container-low relative border-r border-outline-variant/10">
                {/* Document Toolbar */}
                <div className="h-12 flex items-center justify-between px-6 bg-surface-container border-b border-outline-variant/10">
                  <div className="flex items-center gap-4">
                    <span className="text-xs font-bold text-on-surface-variant font-label uppercase tracking-widest">
                      Document
                    </span>
                    <span className="text-sm font-medium text-on-surface">
                      {activeCollection
                        ? `${activeCollection}.pdf`
                        : "No document selected"}
                    </span>
                  </div>
                  {activeCollection && (
                    <div className="flex items-center gap-2">
                      <button className="p-1.5 rounded hover:bg-surface-variant text-on-surface-variant">
                        <span className="material-symbols-outlined text-sm">
                          zoom_out
                        </span>
                      </button>
                      <span className="text-xs font-mono text-on-surface-variant">
                        85%
                      </span>
                      <button className="p-1.5 rounded hover:bg-surface-variant text-on-surface-variant">
                        <span className="material-symbols-outlined text-sm">
                          zoom_in
                        </span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Document Canvas */}
                <div className="flex-1 overflow-y-auto custom-scrollbar bg-surface-container-low p-8 md:p-12">
                  {activeCollection ? (
                    <div className="max-w-2xl mx-auto bg-white shadow-2xl min-h-[900px] p-12 md:p-16 text-[#1a1a1a] relative">
                      <div className="mb-12 border-b-2 border-black pb-4">
                        <h1 className="text-2xl font-headline font-bold uppercase tracking-tighter">
                          {activeCollection}
                        </h1>
                        <p className="text-xs font-bold mt-2">
                          INDEXED DOCUMENT | RAG SYSTEM
                        </p>
                      </div>
                      <div className="space-y-6 text-sm leading-relaxed font-body">
                        <p>
                          This document has been successfully ingested and
                          indexed into the vector database.{" "}
                          <span className="bg-tertiary/40 px-1 border-b-2 border-tertiary">
                            You can now ask questions about its contents using
                            the chat interface.
                          </span>
                        </p>
                        <p>
                          The system uses{" "}
                          <span className="bg-primary/30 px-1">
                            hybrid retrieval
                          </span>{" "}
                          combining dense vector search with cross-encoder
                          reranking.
                        </p>
                        <div className="py-6 flex items-center justify-center">
                          <div className="w-full h-48 bg-gradient-to-br from-gray-100 to-gray-200 rounded flex flex-col items-center justify-center gap-3">
                            <span
                              className="material-symbols-outlined text-5xl text-gray-400"
                              style={{
                                fontVariationSettings: "'FILL' 0, 'wght' 300",
                              }}
                            >
                              description
                            </span>
                            <p className="text-xs text-gray-500 font-medium">
                              Document preview area
                            </p>
                          </div>
                        </div>
                        <p>
                          The retrieval pipeline uses{" "}
                          <span className="bg-tertiary/40 px-1 border-b-2 border-tertiary">
                            cross-encoder reranking
                          </span>{" "}
                          to ensure the most relevant passages are surfaced.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full gap-8">
                      <div
                        onClick={handleUploadClick}
                        onDragOver={(e) => {
                          e.preventDefault();
                          setDragOver(true);
                        }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={(e) => {
                          e.preventDefault();
                          setDragOver(false);
                          const file = e.dataTransfer.files?.[0];
                          if (file) handleUploadFile(file);
                        }}
                        className={
                          "flex cursor-pointer flex-col items-center gap-6 rounded-xl border-2 border-dashed p-16 transition-all max-w-lg w-full " +
                          (dragOver
                            ? "border-primary bg-primary/5 scale-[1.02]"
                            : "border-outline-variant/40 hover:border-primary/40 hover:bg-surface-container")
                        }
                      >
                        {uploading ? (
                          <Spinner size={40} />
                        ) : (
                          <div className="w-20 h-20 rounded-2xl bg-surface-container-high flex items-center justify-center">
                            <span
                              className="material-symbols-outlined text-4xl text-primary"
                              style={{
                                fontVariationSettings: "'FILL' 0, 'wght' 300",
                              }}
                            >
                              cloud_upload
                            </span>
                          </div>
                        )}
                        <div className="text-center">
                          <div className="text-lg font-headline font-semibold text-on-surface">
                            Upload Document
                          </div>
                          <div className="mt-2 text-sm text-on-surface-variant">
                            Drag & drop a PDF or click to browse
                          </div>
                        </div>
                      </div>
                      {uploadError && (
                        <div className="text-sm text-error bg-error-container/20 px-4 py-2 rounded-lg">
                          {uploadError}
                        </div>
                      )}
                      {collections.length > 0 && (
                        <div className="max-w-lg w-full">
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                              Indexed Documents
                            </span>
                            <span className="bg-secondary-container px-2 py-0.5 rounded text-[10px] font-bold text-on-secondary-container">
                              {collections.length}
                            </span>
                          </div>
                          <div className="space-y-1">
                            {collections.map((name) => (
                              <button
                                key={name}
                                type="button"
                                onClick={() => {
                                  setActiveCollection(name);
                                  setOpenCitationIndex(null);
                                }}
                                className={
                                  "flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm transition-all " +
                                  (name === activeCollection
                                    ? "border-l-2 border-secondary bg-surface-container-high text-on-surface"
                                    : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface")
                                }
                              >
                                <span className="material-symbols-outlined text-base">
                                  description
                                </span>
                                <span className="truncate">{name}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Floating Document Controls */}
                {activeCollection && collections.length > 0 && (
                  <div className="absolute left-1/2 -translate-x-1/2 bottom-6 glass-panel p-2 flex items-center gap-2 border border-outline-variant/20 rounded-xl">
                    <button
                      className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors"
                      onClick={() => {
                        const idx = collections.indexOf(activeCollection);
                        if (idx > 0) {
                          setActiveCollection(collections[idx - 1]);
                          setOpenCitationIndex(null);
                        }
                      }}
                    >
                      <span className="material-symbols-outlined">
                        first_page
                      </span>
                    </button>
                    <span className="text-xs font-bold px-4 border-x border-outline-variant/20 whitespace-nowrap">
                      DOC {collections.indexOf(activeCollection) + 1} OF{" "}
                      {collections.length}
                    </span>
                    <button
                      className="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors"
                      onClick={() => {
                        const idx = collections.indexOf(activeCollection);
                        if (idx < collections.length - 1) {
                          setActiveCollection(collections[idx + 1]);
                          setOpenCitationIndex(null);
                        }
                      }}
                    >
                      <span className="material-symbols-outlined">
                        last_page
                      </span>
                    </button>
                  </div>
                )}
              </section>

              {/* ── RIGHT: Chat Interface ── */}
              <section className="flex-[0.8] flex flex-col bg-surface overflow-hidden">
                {/* Chat Feed */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8 flex flex-col">
                  {messages.length === 0 && (
                    <div className="flex-1 flex flex-col items-center justify-center gap-6 animate-fade-in-up">
                      <div
                        className="rounded-2xl bg-surface-container-high p-5"
                        style={{
                          boxShadow: "0 0 40px 8px rgba(151,169,255,0.12)",
                        }}
                      >
                        <span
                          className="material-symbols-outlined text-4xl text-primary"
                          style={{
                            fontVariationSettings: "'FILL' 0, 'wght' 300",
                          }}
                        >
                          auto_awesome
                        </span>
                      </div>
                      <div className="text-center">
                        <h2 className="text-xl font-headline font-bold text-on-surface">
                          Research Assistant
                        </h2>
                        <p className="mt-2 text-sm text-on-surface-variant max-w-sm">
                          {activeCollection
                            ? `Ask questions about "${activeCollection}" — powered by hybrid retrieval & reranking.`
                            : "Upload a document to start your research analysis."}
                        </p>
                      </div>
                      {activeCollection && (
                        <div className="flex flex-col gap-2 w-full max-w-sm">
                          {suggestions.map((text) => (
                            <button
                              key={text}
                              type="button"
                              onClick={() => {
                                setQuestion(text);
                                setTimeout(() => {
                                  setQuestion(text);
                                  handleSend();
                                }, 0);
                              }}
                              className="w-full rounded-xl border border-outline-variant/20 bg-surface-container px-4 py-3 text-left text-sm text-on-surface-variant transition-all hover:border-primary/40 hover:bg-surface-container-high hover:text-on-surface"
                            >
                              {text}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {messages.length > 0 && (
                    <>
                      {messages.map((msg) =>
                        msg.role === "user" ? (
                          <div
                            key={msg.id}
                            className="self-end max-w-[85%] animate-fade-in-up"
                          >
                            <div className="bg-surface-container-high p-4 rounded-xl text-sm leading-relaxed text-on-surface whitespace-pre-wrap break-words">
                              {msg.content}
                            </div>
                            <div className="mt-2 text-[10px] text-on-surface-variant font-bold uppercase tracking-widest text-right">
                              {user?.username || "User"} •{" "}
                              {msg.timestamp || currentTime}
                            </div>
                          </div>
                        ) : (
                          <div
                            key={msg.id}
                            className="self-start max-w-[90%] ai-gradient-border pl-4 animate-fade-in-up"
                          >
                            <div className="space-y-3 text-sm leading-relaxed text-on-surface-variant whitespace-pre-wrap break-words">
                              {msg.content}
                            </div>
                            {Array.isArray(msg.sources) &&
                              msg.sources.length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-1">
                                  {msg.sources.map((s, idx) => (
                                    <CitationPill
                                      key={`${msg.id}-${idx}-${s.page}-${s.source}`}
                                      page={s.page}
                                      distance={s.distance}
                                      isOpen={
                                        openCitationIndex === `${msg.id}:${idx}`
                                      }
                                      onClick={() => {
                                        const key = `${msg.id}:${idx}`;
                                        setOpenCitationIndex((prev) =>
                                          prev === key ? null : key,
                                        );
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            {Array.isArray(msg.sources) &&
                              msg.sources.length > 0 && (
                                <div className="mt-3 flex gap-2">
                                  <div className="bg-surface-container-highest px-3 py-1 rounded-full text-[10px] font-bold text-secondary uppercase tracking-widest flex items-center gap-1">
                                    <span
                                      className="material-symbols-outlined text-[12px]"
                                      style={{
                                        fontVariationSettings: "'FILL' 1",
                                      }}
                                    >
                                      bolt
                                    </span>
                                    Sources: {msg.sources.length}
                                  </div>
                                </div>
                              )}
                            <div className="mt-2 text-[10px] text-on-surface-variant font-bold uppercase tracking-widest">
                              AI Assistant • {msg.timestamp || currentTime}
                            </div>
                          </div>
                        ),
                      )}
                      {chatLoading && (
                        <div className="self-start max-w-[90%] ai-gradient-border pl-4 animate-fade-in-up">
                          <div className="flex items-center gap-3 text-sm text-on-surface-variant">
                            <Spinner size={14} />
                            <span>Processing inference…</span>
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </>
                  )}
                </div>

                {/* Chat Input Area */}
                <div className="p-6 bg-surface-container-low">
                  <div className="max-w-3xl mx-auto space-y-4">
                    <div className="flex items-center justify-between text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">
                      <div className="flex items-center gap-4">
                        <button className="flex items-center gap-1 text-primary">
                          <span className="material-symbols-outlined text-sm">
                            settings_input_component
                          </span>
                          Model: Gemini 1.5 Flash
                        </button>
                        <button className="flex items-center gap-1 hover:text-on-surface transition-colors">
                          <span className="material-symbols-outlined text-sm">
                            layers
                          </span>
                          Context: {activeCollection || "none"}
                        </button>
                      </div>
                      <div className="text-outline">
                        {messages.length} messages
                      </div>
                    </div>
                    <div className="relative group">
                      <div className="absolute inset-0 bg-primary/5 rounded-xl blur-lg transition-opacity opacity-0 group-focus-within:opacity-100" />
                      <div className="relative bg-surface-container-lowest border border-outline-variant/20 group-focus-within:border-primary/40 rounded-xl p-4 flex flex-col gap-3 transition-all">
                        <textarea
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                              e.preventDefault();
                              handleSend();
                            }
                          }}
                          className="bg-transparent border-none focus:ring-0 text-sm placeholder:text-outline-variant resize-none w-full min-h-[80px] text-on-surface"
                          placeholder={
                            activeCollection
                              ? "Ask about the document or research context..."
                              : "Upload a document to start chatting..."
                          }
                          disabled={!activeCollection}
                        />
                        <div className="flex items-center justify-between pt-2 border-t border-outline-variant/10">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={handleUploadClick}
                              className="p-2 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors"
                              title="Attach file"
                            >
                              <span className="material-symbols-outlined">
                                attach_file
                              </span>
                            </button>
                            <button className="p-2 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors">
                              <span className="material-symbols-outlined">
                                mic
                              </span>
                            </button>
                          </div>
                          <button
                            type="button"
                            onClick={handleSend}
                            disabled={
                              !activeCollection ||
                              chatLoading ||
                              !question.trim()
                            }
                            className="bg-gradient-to-br from-primary to-primary-dim text-on-primary-container px-6 py-2 rounded-md font-bold text-xs uppercase tracking-widest hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            Execute Inference
                            <span className="material-symbols-outlined text-sm">
                              send
                            </span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            </>
          )}
        </main>
      </div>

      {/* ═══════ SETTINGS MODAL ═══════ */}
      {showSettings && (
        <SettingsPanel
          onClose={() => setShowSettings(false)}
          user={user}
          onLogout={logout}
        />
      )}

      {/* Upload error toast */}
      {uploadError && activeNav === "chat" && (
        <div className="fixed bottom-4 right-4 bg-error-container text-on-error-container px-4 py-3 rounded-lg shadow-2xl text-sm flex items-center gap-2 animate-fade-in-up z-50">
          <span className="material-symbols-outlined text-lg">error</span>
          {uploadError}
          <button
            onClick={() => setUploadError("")}
            className="ml-2 hover:opacity-70"
          >
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}
    </div>
  );
}

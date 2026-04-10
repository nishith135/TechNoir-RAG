import { useState } from "react";
import { useAuth } from "./AuthContext";

export default function LoginPage({ onSwitchToRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6 font-body">
      {/* Background glow effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-headline font-bold tracking-tighter text-primary">
            Tech Noir RAG
          </h1>
          <p className="text-on-surface-variant text-sm mt-2">
            Research Suite — AI Engine v2.4
          </p>
        </div>

        {/* Card */}
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-8 shadow-2xl">
          <h2 className="text-xl font-headline font-bold text-on-surface mb-1">
            Welcome back
          </h2>
          <p className="text-sm text-on-surface-variant mb-8">
            Sign in to continue your research
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                Email
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-lg text-outline">
                  mail
                </span>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/20 focus:border-primary/60 rounded-lg pl-10 pr-4 py-3 text-sm text-on-surface placeholder:text-outline-variant outline-none transition-colors"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-lg text-outline">
                  lock
                </span>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/20 focus:border-primary/60 rounded-lg pl-10 pr-4 py-3 text-sm text-on-surface placeholder:text-outline-variant outline-none transition-colors"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 text-sm text-error bg-error-container/20 px-4 py-2.5 rounded-lg">
                <span className="material-symbols-outlined text-base">
                  error
                </span>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-br from-primary to-primary-dim text-on-primary-container py-3 rounded-lg font-headline font-bold text-sm uppercase tracking-widest hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
                  Authenticating…
                </>
              ) : (
                <>
                  Sign In
                  <span className="material-symbols-outlined text-base">
                    arrow_forward
                  </span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 h-px bg-outline-variant/20" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-outline">
              or
            </span>
            <div className="flex-1 h-px bg-outline-variant/20" />
          </div>

          {/* Switch to register */}
          <button
            id="switch-to-register"
            type="button"
            onClick={onSwitchToRegister}
            className="w-full border border-outline-variant/20 text-on-surface-variant py-3 rounded-lg text-sm font-medium hover:bg-surface-container-high hover:text-on-surface transition-all"
          >
            Create a new account
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] text-outline mt-6 uppercase tracking-widest">
          Powered by RAG • Hybrid Retrieval • Reranking
        </p>
      </div>
    </div>
  );
}

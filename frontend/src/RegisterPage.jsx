import { useState } from "react";
import { useAuth } from "./AuthContext";

export default function RegisterPage({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await register(username, email, password);
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
        <div className="absolute top-1/3 right-1/3 w-96 h-96 bg-secondary/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/3 left-1/3 w-80 h-80 bg-tertiary/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-headline font-bold tracking-tighter text-primary">
            Tech Noir RAG
          </h1>
          <p className="text-on-surface-variant text-sm mt-2">
            Create your research account
          </p>
        </div>

        {/* Card */}
        <div className="bg-surface-container border border-outline-variant/20 rounded-xl p-8 shadow-2xl">
          <h2 className="text-xl font-headline font-bold text-on-surface mb-1">
            Get started
          </h2>
          <p className="text-sm text-on-surface-variant mb-8">
            Set up your credentials to begin
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                Username
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-lg text-outline">
                  person
                </span>
                <input
                  id="register-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/20 focus:border-primary/60 rounded-lg pl-10 pr-4 py-3 text-sm text-on-surface placeholder:text-outline-variant outline-none transition-colors"
                  placeholder="researcher_01"
                  required
                  minLength={2}
                />
              </div>
            </div>

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
                  id="register-email"
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
                  id="register-password"
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

            {/* Confirm Password */}
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-lg text-outline">
                  lock
                </span>
                <input
                  id="register-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
              id="register-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-br from-primary to-primary-dim text-on-primary-container py-3 rounded-lg font-headline font-bold text-sm uppercase tracking-widest hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
                  Creating account…
                </>
              ) : (
                <>
                  Create Account
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

          {/* Switch to login */}
          <button
            id="switch-to-login"
            type="button"
            onClick={onSwitchToLogin}
            className="w-full border border-outline-variant/20 text-on-surface-variant py-3 rounded-lg text-sm font-medium hover:bg-surface-container-high hover:text-on-surface transition-all"
          >
            Already have an account? Sign in
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

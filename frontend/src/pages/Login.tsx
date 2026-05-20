import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowRight, Loader2 } from "lucide-react";
import { authApi } from "../api/client";
import { useAuthStore } from "../stores/authStore";
import PipeForgeLogo from "../components/PipeForgeLogo";

/* Feature list — custom minimal SVG icons, not library icons */
const FEATURES: { icon: React.ReactNode; title: string; desc: string }[] = [
  {
    icon: (
      /* NL prompt → pipeline: a cursor/text symbol */
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M2 4h12M2 8h8M2 12h5" stroke="rgba(255,255,255,0.8)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M12 10l2 2-2 2" stroke="#6366F1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: "Natural language → pipeline",
    desc: "Describe your transformation in plain English",
  },
  {
    icon: (
      /* DAG: nodes connected — represents visual graph editor */
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="3"  cy="8"  r="2"   fill="rgba(255,255,255,0.8)" />
        <circle cx="13" cy="4"  r="1.75" fill="#6366F1" />
        <circle cx="13" cy="12" r="1.75" fill="rgba(255,255,255,0.55)" />
        <line x1="5" y1="7.2"  x2="11" y2="4.5"  stroke="rgba(255,255,255,0.35)" strokeWidth="1" strokeLinecap="round"/>
        <line x1="5" y1="8.8"  x2="11" y2="11.5" stroke="rgba(255,255,255,0.35)" strokeWidth="1" strokeLinecap="round"/>
      </svg>
    ),
    title: "Visual DAG editor",
    desc: "See your pipeline as an interactive graph",
  },
  {
    icon: (
      /* Pulse/waveform — execution monitoring */
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1 8h2.5l2-4 2.5 8 2-5.5L12 8h3" stroke="rgba(255,255,255,0.8)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="14.5" cy="8" r="1" fill="#6366F1"/>
      </svg>
    ),
    title: "Real-time execution logs",
    desc: "Watch each step execute with live streaming",
  },
];

export default function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data: token } = await authApi.login(email, password);
      const { data: user } = await authApi.me(token.access_token);
      setAuth(token.access_token, { id: user.id, email: user.email });
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Login failed. Check your credentials.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black flex">

      {/* ── Left branding panel ── */}
      <div className="hidden lg:flex lg:w-[46%] relative flex-col items-start justify-center px-14 py-12 overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-[500px] h-[500px]"
            style={{ background: "radial-gradient(circle at 30% 30%, rgba(99,102,241,0.1) 0%, transparent 65%)" }} />
          <div className="absolute bottom-0 right-0 w-[300px] h-[300px]"
            style={{ background: "radial-gradient(circle at 70% 70%, rgba(99,102,241,0.06) 0%, transparent 65%)" }} />
        </div>

        {/* Very subtle grid */}
        <div className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />

        {/* Right edge */}
        <div className="absolute right-0 inset-y-8"
          style={{ width: 1, background: "linear-gradient(to bottom, transparent, rgba(255,255,255,0.07) 30%, rgba(255,255,255,0.07) 70%, transparent)" }}
        />

        <div className="relative z-10 max-w-[380px]">
          {/* Logo */}
          <div className="mb-12">
            <PipeForgeLogo size="lg" />
          </div>

          <h2 className="text-[2.4rem] font-bold text-white leading-[1.12] tracking-[-0.02em] mb-4">
            Turn plain English<br />into production<br />pipelines.
          </h2>
          <p className="text-white/40 text-sm leading-[1.7] mb-10">
            Describe any data transformation. PipeForge generates, visualizes, and runs it — no engineering required.
          </p>

          {/* Feature list — no square containers, clean and minimal */}
          <div className="space-y-5">
            {FEATURES.map(({ icon, title, desc }) => (
              <div key={title} className="flex items-start gap-3.5">
                <div className="mt-0.5 shrink-0 w-5 h-5 flex items-center justify-center">
                  {icon}
                </div>
                <div>
                  <p className="text-white/80 text-sm font-medium leading-none mb-1">{title}</p>
                  <p className="text-white/35 text-xs leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Subtle right-side glow */}
        <div className="absolute top-0 right-0 w-[400px] h-[400px] pointer-events-none"
          style={{ background: "radial-gradient(circle at top right, rgba(99,102,241,0.05) 0%, transparent 60%)" }}
        />

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.28, ease: "easeOut" }}
          className="w-full max-w-[340px] relative"
        >
          {/* Mobile logo */}
          <div className="mb-10 lg:hidden">
            <PipeForgeLogo size="md" />
          </div>

          <h1 className="text-[1.6rem] font-bold text-white mb-1 tracking-tight">Sign in</h1>
          <p className="text-white/40 text-sm mb-8">Access your data pipelines</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg px-3.5 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none transition"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
                onFocus={(e) => { e.target.style.border = "1px solid rgba(99,102,241,0.5)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.08)"; }}
                onBlur={(e)  => { e.target.style.border = "1px solid rgba(255,255,255,0.08)"; e.target.style.boxShadow = "none"; }}
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg px-3.5 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none transition"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
                onFocus={(e) => { e.target.style.border = "1px solid rgba(99,102,241,0.5)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.08)"; }}
                onBlur={(e)  => { e.target.style.border = "1px solid rgba(255,255,255,0.08)"; e.target.style.boxShadow = "none"; }}
                placeholder="••••••••"
              />
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              className="w-full mt-2 py-2.5 px-4 text-sm font-semibold rounded-lg text-white disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              style={{
                background: "linear-gradient(135deg, #5B5EEA 0%, #7C3FD4 100%)",
                boxShadow: "0 0 0 1px rgba(99,102,241,0.4), 0 4px 24px rgba(99,102,241,0.25)",
              }}
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Signing in…</>
                : <><span>Sign in</span><ArrowRight size={13} /></>
              }
            </motion.button>
          </form>

          <div className="mt-7 pt-6 text-center" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            <p className="text-sm text-white/35">
              No account?{" "}
              <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                Create one free →
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

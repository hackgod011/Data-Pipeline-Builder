import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowRight, Loader2 } from "lucide-react";
import { authApi } from "../api/client";
import { useAuthStore } from "../stores/authStore";
import PipeForgeLogo from "../components/PipeForgeLogo";

const PERKS = [
  { label: "Free account",         sub: "No credit card required" },
  { label: "First pipeline in 5m", sub: "Upload a file and describe what you want" },
  { label: "Quality reports",      sub: "Automatic data profiling on every run" },
];

export default function Register() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { toast.error("Passwords do not match."); return; }
    if (password.length < 8) { toast.error("Password must be at least 8 characters."); return; }
    setLoading(true);
    try {
      await authApi.register(email, password);
      const { data: token } = await authApi.login(email, password);
      const { data: user } = await authApi.me(token.access_token);
      setAuth(token.access_token, { id: user.id, email: user.email });
      toast.success("Account created! Welcome to PipeForge.");
      navigate("/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
  };
  const inputFocusOn  = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.border = "1px solid rgba(99,102,241,0.5)";
    e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.08)";
  };
  const inputFocusOff = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.border = "1px solid rgba(255,255,255,0.08)";
    e.target.style.boxShadow = "none";
  };

  return (
    <div className="min-h-screen bg-black flex">

      {/* ── Left branding panel ── */}
      <div className="hidden lg:flex lg:w-[46%] relative flex-col items-start justify-center px-14 py-12 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-[500px] h-[500px]"
            style={{ background: "radial-gradient(circle at 30% 30%, rgba(99,102,241,0.1) 0%, transparent 65%)" }} />
        </div>
        <div className="absolute inset-0 pointer-events-none"
          style={{ backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)", backgroundSize: "32px 32px" }}
        />
        <div className="absolute right-0 inset-y-8"
          style={{ width: 1, background: "linear-gradient(to bottom, transparent, rgba(255,255,255,0.07) 30%, rgba(255,255,255,0.07) 70%, transparent)" }}
        />

        <div className="relative z-10 max-w-[380px]">
          <div className="mb-12">
            <PipeForgeLogo size="lg" />
          </div>

          <h2 className="text-[2.4rem] font-bold text-white leading-[1.12] tracking-[-0.02em] mb-4">
            Start building<br />pipelines in<br />minutes.
          </h2>
          <p className="text-white/40 text-sm leading-[1.7] mb-10">
            No data engineering experience needed. Just describe what you want.
          </p>

          <div className="space-y-5">
            {PERKS.map(({ label, sub }, i) => (
              <div key={label} className="flex items-start gap-3.5">
                {/* Numbered indicator */}
                <div
                  className="shrink-0 mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                  style={{
                    background: "rgba(99,102,241,0.15)",
                    border: "1px solid rgba(99,102,241,0.3)",
                    color: "#818CF8",
                  }}
                >
                  {i + 1}
                </div>
                <div>
                  <p className="text-white/80 text-sm font-medium leading-none mb-1">{label}</p>
                  <p className="text-white/35 text-xs leading-relaxed">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
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
          <div className="mb-10 lg:hidden">
            <PipeForgeLogo size="md" />
          </div>

          <h1 className="text-[1.6rem] font-bold text-white mb-1 tracking-tight">Create account</h1>
          <p className="text-white/40 text-sm mb-8">Free forever — no card required</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {([
              { id: "email",    label: "Email",            type: "email",    value: email,    set: setEmail,    ph: "you@company.com" },
              { id: "pw",       label: "Password",         type: "password", value: password, set: setPassword, ph: "min 8 characters" },
              { id: "confirm",  label: "Confirm Password", type: "password", value: confirm,  set: setConfirm,  ph: "repeat password"  },
            ] as const).map(({ id, label, type, value, set, ph }) => (
              <div key={id}>
                <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">{label}</label>
                <input
                  type={type}
                  required
                  value={value}
                  onChange={(e) => set(e.target.value)}
                  className="w-full rounded-lg px-3.5 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none transition"
                  style={inputStyle}
                  onFocus={inputFocusOn}
                  onBlur={inputFocusOff}
                  placeholder={ph}
                />
              </div>
            ))}

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
                ? <><Loader2 size={14} className="animate-spin" /> Creating account…</>
                : <><span>Create account</span><ArrowRight size={13} /></>
              }
            </motion.button>
          </form>

          <div className="mt-7 pt-6 text-center" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            <p className="text-sm text-white/35">
              Already have an account?{" "}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                Sign in →
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

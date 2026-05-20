import { useNavigate, useLocation } from "react-router-dom";
import { LayoutDashboard, History, CalendarClock, LogOut } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { PipeForgeIcon } from "./PipeForgeLogo";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { label: "History",   path: "/history",   icon: History },
  { label: "Schedules", path: "/schedules", icon: CalendarClock },
];

export default function AppNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearAuth } = useAuthStore();

  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : "??";

  return (
    <header
      className="h-14 flex items-center justify-between px-5 shrink-0 sticky top-0 z-40"
      style={{
        background: "rgba(0,0,0,0.75)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* Left: logo + nav */}
      <div className="flex items-center gap-6">
        <button onClick={() => navigate("/dashboard")} className="group">
          <div
            className="flex items-center gap-2.5 px-1 py-0.5"
          >
            <div
              className="w-[28px] h-[28px] rounded-lg flex items-center justify-center shrink-0 transition-all group-hover:shadow-indigo-900/40"
              style={{
                background: "linear-gradient(145deg, #1A1A2E 0%, #0D0D1A 100%)",
                boxShadow: "0 0 0 1px rgba(99,102,241,0.28), 0 0 12px rgba(99,102,241,0.10)",
              }}
            >
              <PipeForgeIcon size={16} />
            </div>
            <span className="text-white font-semibold text-sm tracking-tight">PipeForge</span>
          </div>
        </button>

        <nav className="flex items-center gap-0.5">
          {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${active
                    ? "text-white bg-white/[0.06] shadow-sm"
                    : "text-white/40 hover:text-white/80 hover:bg-white/[0.04]"
                  }
                `}
              >
                <Icon size={13} strokeWidth={active ? 2.5 : 2} />
                {label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Right: avatar + sign out */}
      <div className="flex items-center gap-3">
        {/* User avatar */}
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center cursor-default"
          style={{
            background: "rgba(99,102,241,0.15)",
            border: "1px solid rgba(99,102,241,0.25)",
          }}
          title={user?.email ?? ""}
        >
          <span className="text-[10px] font-semibold text-indigo-300 leading-none">{initials}</span>
        </div>

        <div
          className="w-px h-4"
          style={{ background: "rgba(255,255,255,0.08)" }}
        />

        <button
          onClick={() => { clearAuth(); navigate("/login"); }}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-white/35 hover:text-red-400 hover:bg-red-500/08 transition-all"
        >
          <LogOut size={12} strokeWidth={2} />
          <span>Sign out</span>
        </button>
      </div>
    </header>
  );
}

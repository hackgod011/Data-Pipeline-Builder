/**
 * PipeForge logo — a minimal DAG: one source node branching into two outputs,
 * representing a data pipeline. Geometric, not icon-library, not AI-generated.
 */
interface Props {
  size?: number;
}

export function PipeForgeIcon({ size = 18 }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* Pipeline lines */}
      <line x1="7" y1="10" x2="12" y2="5.5"  stroke="rgba(255,255,255,0.45)" strokeWidth="1"   strokeLinecap="round" />
      <line x1="7" y1="10" x2="12" y2="14.5" stroke="rgba(255,255,255,0.45)" strokeWidth="1"   strokeLinecap="round" />
      <line x1="3.5" y1="10" x2="6.5" y2="10" stroke="rgba(255,255,255,0.45)" strokeWidth="1" strokeLinecap="round" />

      {/* Source node — left, indigo filled */}
      <circle cx="3.5" cy="10" r="2"   fill="#6366F1" />
      {/* Intermediate node — center */}
      <circle cx="7"   cy="10" r="1.5" fill="rgba(255,255,255,0.85)" />
      {/* Output node top */}
      <circle cx="13"  cy="5.5"  r="1.75" fill="white" />
      {/* Output node bottom */}
      <circle cx="13"  cy="14.5" r="1.75" fill="rgba(255,255,255,0.65)" />
    </svg>
  );
}

interface LogoProps {
  size?: "sm" | "md" | "lg";
}

export default function PipeForgeLogo({ size = "md" }: LogoProps) {
  const iconSize = size === "sm" ? 16 : size === "md" ? 18 : 22;
  const containerSize = size === "sm" ? 28 : size === "md" ? 32 : 40;
  const textClass = size === "sm"
    ? "text-sm font-semibold"
    : size === "md"
    ? "text-sm font-semibold"
    : "text-xl font-bold";

  return (
    <div className="flex items-center gap-2.5">
      {/* Logo mark — dark square with DAG inside */}
      <div
        className="shrink-0 rounded-xl flex items-center justify-center"
        style={{
          width: containerSize,
          height: containerSize,
          background: "linear-gradient(145deg, #1A1A2E 0%, #0D0D1A 100%)",
          boxShadow: "0 0 0 1px rgba(99,102,241,0.3), 0 0 16px rgba(99,102,241,0.12)",
        }}
      >
        <PipeForgeIcon size={iconSize} />
      </div>
      <span className={`text-white tracking-tight ${textClass}`}>PipeForge</span>
    </div>
  );
}

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface Props { children: ReactNode }

export default function PageTransition({ children }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="min-h-screen flex flex-col relative"
      style={{ background: "transparent" }}
    >
      {/* Indigo nebula — top left */}
      <div
        aria-hidden
        className="pointer-events-none fixed top-0 left-0 w-[700px] h-[700px] opacity-[0.08]"
        style={{ background: "radial-gradient(circle at 20% 20%, #6366F1 0%, transparent 60%)" }}
      />
      {/* Violet nebula — bottom right */}
      <div
        aria-hidden
        className="pointer-events-none fixed bottom-0 right-0 w-[500px] h-[500px] opacity-[0.05]"
        style={{ background: "radial-gradient(circle at 80% 80%, #8B5CF6 0%, transparent 60%)" }}
      />
      {children}
    </motion.div>
  );
}

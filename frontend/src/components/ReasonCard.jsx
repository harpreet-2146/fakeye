import React from "react";
import { motion } from "framer-motion";

export default function ReasonCard({ reason = "" }) {
  if (!reason) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="
        relative overflow-hidden rounded-2xl 
        border border-indigo-500/30
        bg-gradient-to-br from-indigo-500/15 via-sky-500/10 to-cyan-400/10
        p-5
      "
    >
      {/* Subtle glow */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-indigo-400/10 via-transparent to-cyan-400/10" />

      {/* Header */}
      <div className="relative flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-full bg-indigo-500/20 flex items-center justify-center">
          <span className="text-indigo-300 text-lg">💡</span>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-indigo-300">
            Reasoning
          </div>
          <div className="text-sm text-slate-400">
            Why this conclusion was reached
          </div>
        </div>
      </div>

      {/* Reason text */}
      <p className="relative text-sm text-slate-100 leading-relaxed">
        {reason}
      </p>

      {/* Footer */}
      <div className="relative mt-4 flex items-center gap-2 text-xs text-slate-400">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400" />
        Based on strongest supporting or contradicting evidence
      </div>
    </motion.div>
  );
}

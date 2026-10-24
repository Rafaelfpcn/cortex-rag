"use client";

import React, { useState } from "react";
import { Citation } from "@/types";

interface Props {
  citation: Citation;
  index: number;
}

export const CitationBadge: React.FC<Props> = ({ citation, index }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 hover:border-indigo-500/50 px-2 py-0.5 rounded transition-colors"
      >
        [Fonte {index}: {citation.document_title} (Pág. {citation.page ?? 1})]
      </button>

      {open && (
        <div className="absolute z-20 bottom-full left-0 mb-2 w-80 p-3 bg-slate-900 border border-slate-700 rounded-lg shadow-xl text-xs text-slate-300">
          <div className="flex items-center justify-between font-semibold text-white border-b border-slate-800 pb-1 mb-2">
            <span className="truncate">{citation.document_title}</span>
            <span className="text-[10px] text-indigo-400">RRF: {citation.score.toFixed(4)}</span>
          </div>
          <p className="italic text-slate-400 font-serif leading-relaxed mb-2 text-[11px]">
            &ldquo;{citation.snippet}&rdquo;
          </p>
          <div className="flex justify-between items-center text-[10px] text-slate-500">
            <span>Página estimada: {citation.page ?? 1}</span>
            <button
              onClick={() => setOpen(false)}
              className="text-indigo-400 hover:underline"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

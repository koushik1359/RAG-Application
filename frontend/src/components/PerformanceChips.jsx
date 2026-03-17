import React from 'react';
import { Search, Target, Cpu, Zap } from 'lucide-react';

export default function PerformanceChips({ performance }) {
  if (!performance) return null;

  return (
    <div className="px-5 pb-4 pt-1 border-t border-slate-700/50 mt-1">
      <div className="flex flex-wrap gap-2 text-xs font-medium tracking-wide">
        <span className="flex items-center gap-1 bg-slate-900 border border-slate-700 text-slate-400 px-2 py-1 rounded-full">
          <Search size={10} className="text-indigo-400" />
          Retrieval: {performance.retrieval_ms}ms
        </span>
        <span className="flex items-center gap-1 bg-slate-900 border border-slate-700 text-slate-400 px-2 py-1 rounded-full">
          <Target size={10} className="text-rose-400" />
          Re-Rank: {performance.reranking_ms}ms
        </span>
        <span className="flex items-center gap-1 bg-slate-900 border border-slate-700 text-slate-400 px-2 py-1 rounded-full">
          <Cpu size={10} className="text-purple-400" />
          LLM: {performance.llm_ms}ms
        </span>
        <span className="flex items-center gap-1 bg-emerald-950 border border-emerald-900 text-emerald-400 px-2 py-1 rounded-full">
          <Zap size={10} />
          Total: {performance.total_ms}ms
        </span>
      </div>
    </div>
  );
}

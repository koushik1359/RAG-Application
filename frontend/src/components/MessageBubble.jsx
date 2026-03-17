import React from 'react';
import { FileText } from 'lucide-react';
import { marked } from 'marked';
import PerformanceChips from './PerformanceChips';

// Configure marked
marked.setOptions({ breaks: true, gfm: true });

function safeMarked(content) {
  try {
    if (!content) return '';
    return marked(String(content));
  } catch (e) {
    return String(content);
  }
}

export default function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  const isSystem = msg.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-end">
        <div className="bg-indigo-900/30 text-indigo-300 border border-indigo-500/30 px-4 py-2 rounded-lg text-sm shadow-sm flex items-center gap-2">
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl shadow-sm border ${
        isUser 
          ? 'bg-userMessage border-indigo-500/30 text-indigo-50 rounded-tr-sm' 
          : 'bg-aiMessage border-border text-slate-200 rounded-tl-sm'
      }`}>
        
        {/* Content */}
        <div 
          className="p-4 md:p-5 max-w-none leading-relaxed prose prose-invert prose-slate"
          dangerouslySetInnerHTML={{ __html: safeMarked(msg.content) }}
        />

        {/* Sources */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="px-5 pb-4">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <FileText size={12} />
              Sources Used
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {msg.sources.map((src, i) => (
                <div key={i} className="bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-xs hover:border-slate-600 transition-colors">
                  <div className="font-medium text-indigo-300 flex items-center gap-1.5 mb-1.5 truncate">
                    <FileText size={12} className="shrink-0" />
                    <span className="truncate">{src.source || 'Unknown'}</span>
                    <span className="text-slate-500 ml-auto shrink-0 bg-slate-800 px-1.5 py-0.5 rounded">Pg {src.page || '?'}</span>
                  </div>
                  <div className="text-slate-400 line-clamp-2 leading-relaxed italic border-l-2 border-slate-700 pl-2">
                    &quot;{src.content || ''}&quot;
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <PerformanceChips performance={msg.performance} />
      </div>
    </div>
  );
}

import React from 'react';
import { Trash2, Cpu, TerminalSquare, Send } from 'lucide-react';
import MessageBubble from './MessageBubble';

export default function ChatArea({ 
  messages, 
  loading, 
  input, 
  setInput, 
  onSend, 
  onClearChat, 
  chatEndRef 
}) {
  return (
    <div className="flex-1 flex flex-col bg-slate-900 relative">
      
      {/* Header */}
      <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-surface shadow-sm z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full" style={{boxShadow: '0 0 8px rgba(16,185,129,0.5)'}}></div>
          <h1 className="font-semibold text-lg tracking-wide">Enterprise RAG Engine</h1>
        </div>
        <button 
          onClick={onClearChat}
          className="flex items-center gap-2 text-sm text-textMuted hover:text-white transition-colors bg-slate-800 px-3 py-1.5 rounded-md border border-slate-700"
        >
          <Trash2 size={14} />
          Clear Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth">
        {messages.map((msg, index) => (
          <MessageBubble key={index} msg={msg} />
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-aiMessage border border-border rounded-xl p-4 shadow-sm flex items-center gap-3">
              <Cpu size={18} className="text-primary animate-pulse" />
              <span className="text-textMuted text-sm animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 md:p-6 bg-transparent shrink-0">
        <form 
          onSubmit={onSend}
          className="max-w-4xl mx-auto relative flex items-center bg-surface border border-slate-700 rounded-xl shadow-lg focus-within:border-primary transition-all overflow-hidden"
        >
          <div className="pl-4 text-slate-500">
            <TerminalSquare size={20} />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={loading}
            className="flex-1 bg-transparent border-none py-4 px-4 text-white focus:outline-none placeholder-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-3 mr-2 bg-primary hover:bg-primaryHover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}

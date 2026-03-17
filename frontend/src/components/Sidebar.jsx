import React from 'react';
import { ShieldAlert, Upload, FileText, Plus, Trash2 } from 'lucide-react';

export default function Sidebar({ 
  documents, 
  uploading, 
  onUpload, 
  onClearAll, 
  fileInputRef 
}) {
  return (
    <div className="w-80 bg-surface border-r border-border flex flex-col shadow-xl z-10 shrink-0">
      <div className="p-5 border-b border-border flex justify-between items-center" style={{backgroundColor: 'rgba(15,23,42,0.5)'}}>
        <div className="flex items-center gap-2 font-bold tracking-wide text-sm text-slate-300">
          <ShieldAlert size={16} className="text-primary" />
          KNOWLEDGE BASE
        </div>
        <span className="bg-primary text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {documents.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
        {documents.length === 0 ? (
          <div className="text-center text-textMuted mt-10 p-6 border border-dashed border-border rounded-xl" style={{backgroundColor: 'rgba(15,23,42,0.3)'}}>
            <Upload size={32} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">No documents yet</p>
            <p className="text-xs opacity-70 mt-1">Upload PDF, DOCX, TXT, or CSV</p>
          </div>
        ) : (
          documents.map((doc, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700 shadow-sm hover:border-slate-600 transition-colors">
              <FileText size={18} className="text-indigo-400 shrink-0" />
              <span className="text-sm truncate opacity-90">{typeof doc === 'object' ? doc.name : String(doc)}</span>
              {doc.size_kb && <span className="text-[10px] text-slate-500 ml-auto">{doc.size_kb}KB</span>}
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-border flex flex-col gap-3" style={{backgroundColor: 'rgba(15,23,42,0.5)'}}>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={onUpload} 
          className="hidden" 
          accept=".pdf,.docx,.txt,.csv"
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center justify-center gap-2 w-full py-2.5 bg-primary hover:bg-primaryHover text-white rounded-lg font-medium transition-colors shadow-md disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {uploading ? <span className="animate-spin">⏳</span> : <Plus size={18} />}
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
        
        <button 
          onClick={onClearAll}
          className="flex items-center justify-center gap-2 w-full py-2.5 bg-transparent border border-red-900 hover:bg-red-900/20 text-red-400 rounded-lg font-medium transition-colors"
        >
          <Trash2 size={16} />
          <span>Clear All Data</span>
        </button>
      </div>
    </div>
  );
}

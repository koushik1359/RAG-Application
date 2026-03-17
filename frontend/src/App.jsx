import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { API_URL, ACCESS_TOKEN } from './constants';

function App() {
  const [messages, setMessages] = useState([{
    role: 'ai',
    content: "Hello! I am connected to your enterprise knowledge base.\n\nUpload a document using the sidebar, then ask me any question. I will search through your documents and cite my sources."
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Load documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const updateAiContent = (id, newContent) => {
    setMessages(prev => prev.map(m => 
      m.id === id ? { ...m, content: newContent } : m
    ));
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents/`, {
         headers: { 'access_token': ACCESS_TOKEN }
      });
      if (!response.ok) throw new Error("Failed");
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      setDocuments([]);
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'ai',
      content: "Chat history cleared. How can I help you today?"
    }]);
  };

  const clearAllData = async () => {
    if (!window.confirm("Are you sure you want to delete ALL documents and chat history? This cannot be undone.")) return;
    
    try {
      const resp = await fetch(`${API_URL}/documents/clear`, { 
        method: 'POST',
        headers: { 'access_token': ACCESS_TOKEN }
      });
      if (resp.ok) {
        setDocuments([]);
        clearChat();
        setMessages(prev => [...prev, { role: 'system', content: '✅ All data cleared successfully.' }]);
      }
    } catch (error) {
       console.error("Failed to clear data:", error);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setMessages(prev => [...prev, { 
      role: 'system', 
      content: `Uploading: ${file.name}...` 
    }]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload/`, {
        method: 'POST',
        headers: { 'access_token': ACCESS_TOKEN },
        body: formData
      });
      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev.slice(0, -1), { 
          role: 'system', 
          content: `✅ Successfully uploaded: ${file.name}` 
        }]);
        fetchDocuments();
      } else {
        throw new Error(data.detail || "Upload failed");
      }
    } catch (error) {
      setMessages(prev => [...prev.slice(0, -1), { 
        role: 'system', 
        content: `❌ Error uploading: ${error.message}` 
      }]);
    } finally {
      setUploading(false);
      if (e.target) e.target.value = '';
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    
    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const historyItems = messages
        .filter(m => m.role === 'user' || m.role === 'ai')
        .map(m => ({ role: m.role, content: m.content }));

      const response = await fetch(`${API_URL}/chat/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'access_token': ACCESS_TOKEN 
        },
        body: JSON.stringify({ message: userText, history: historyItems })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Unable to reach the FastAPI server.");
      }

      // --- Streaming Logic ---
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let metadataParsed = false;
      let aiMsgId = Date.now(); // Unique ID for finding the message in state

      // Add actual AI message placeholder
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: '',
        sources: [],
        performance: null,
        id: aiMsgId
      }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // Handle metadata chunk (contains |||)
        if (!metadataParsed && chunk.includes('|||')) {
          const parts = chunk.split('|||');
          try {
            const metadata = JSON.parse(parts[0]);
            setMessages(prev => prev.map(m => 
              m.id === aiMsgId 
                ? { ...m, sources: metadata.sources, performance: metadata.performance } 
                : m
            ));
          } catch (e) {
            console.error("Metadata parse error:", e);
          }
          metadataParsed = true;
          if (parts[1]) {
            fullContent += parts[1];
            updateAiContent(aiMsgId, fullContent);
          }
        } else if (chunk.includes('|||')) {
          // Final metadata chunk
          const parts = chunk.split('|||');
          if (parts[0]) {
            fullContent += parts[0];
            updateAiContent(aiMsgId, fullContent);
          }
          try {
            const finalData = JSON.parse(parts[1]);
            if (finalData.type === 'final_metadata') {
              setMessages(prev => prev.map(m => 
                m.id === aiMsgId 
                  ? { ...m, performance: { ...m.performance, ...finalData.performance } } 
                  : m
              ));
            }
          } catch (e) {
            console.error("Final metadata parse error:", e);
          }
        } else {
          // Regular token chunk
          fullContent += chunk;
          updateAiContent(aiMsgId, fullContent);
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'system', 
        content: `⚠️ Error: ${error.message}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-textMain overflow-hidden font-sans">
      <Sidebar 
        documents={documents}
        uploading={uploading}
        onUpload={handleUpload}
        onClearAll={clearAllData}
        fileInputRef={fileInputRef}
      />
      
      <ChatArea 
        messages={messages}
        loading={loading}
        input={input}
        setInput={setInput}
        onSend={handleSendMessage}
        onClearChat={clearChat}
        chatEndRef={chatEndRef}
      />
    </div>
  );
}

export default App;

# 🗄️ Enterprise RAG Engine — Chat With Your Documents

> An end-to-end Retrieval-Augmented Generation (RAG) application that lets you upload documents, embed them into a cloud vector database, and ask natural-language questions — with **page-level source citations** and **conversational memory**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.3-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-VectorDB-purple)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--Turbo-412991?logo=openai)

---

## ✨ Features

| Feature | Description |
|---|---|
| **📄 Multi-Format Upload** | Upload PDF, DOCX, TXT, and CSV files directly from the browser. |
| **🔍 Semantic Search** | Hugging Face `all-MiniLM-L6-v2` embeddings for intelligent document retrieval. |
| **🧠 Conversational Memory** | Follow-up questions understand context — "What are his skills?" just works. |
| **📑 Source Citations** | Every answer includes the exact **file name** and **page number**. |
| **📁 Document Management** | Sidebar with file list, per-document delete, and "Clear All" database wipe. |
| **📝 Markdown Rendering** | AI responses render tables, code blocks, lists, and headings beautifully. |
| **📊 Upload Progress Bar** | Visual feedback with labeled stages during document processing. |
| **☁️ Cloud Vector Store** | Pinecone for fast, scalable similarity search across thousands of documents. |

---

## 🏗️ Architecture

```
┌──────────────┐     File Upload      ┌──────────────────┐
│   Frontend   │ ──────────────────► │  FastAPI Backend  │
│  (HTML/JS)   │  PDF/DOCX/TXT/CSV   │    /upload        │
└──────┬───────┘                     └────────┬─────────┘
       │                                      │
       │  User Question                       │ Chunk → Embed → Store
       │  + Chat History                      ▼
       │                             ┌──────────────────┐
       │  POST /chat                 │     Pinecone      │
       └───────────────────────────► │  Vector Database   │
                                     └────────┬─────────┘
                                              │
                                              │ Top-K Similar Chunks
                                              ▼
                                     ┌──────────────────┐
                                     │   OpenAI GPT-3.5  │
                                     │  + Chat History   │
                                     └──────────────────┘
                                              │
                                              │ Answer + Citations
                                              ▼
                                     ┌──────────────────┐
                                     │   Frontend Chat   │
                                     │  Markdown + Cites │
                                     └──────────────────┘
```

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI (modular router architecture)
- **Orchestration:** LangChain (history-aware retrieval chain)
- **Vector Database:** Pinecone (Cloud)
- **Embeddings:** Hugging Face `all-MiniLM-L6-v2` (local, free)
- **LLM:** OpenAI GPT-3.5-Turbo
- **Frontend:** HTML, CSS, JavaScript (Dark Mode + Markdown via marked.js)

---

## 📁 Project Structure

```
enterprice_rag/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI app, CORS, router registration
│   ├── config.py             # Environment variables & constants
│   ├── models.py             # Pydantic request/response models
│   ├── rag_engine.py         # Embeddings, LLM, Pinecone, RAG chain
│   └── routers/
│       ├── __init__.py
│       ├── chat.py           # POST /chat — conversational Q&A
│       ├── upload.py         # POST /upload — multi-format ingestion
│       └── documents.py      # GET/DELETE /documents — management
├── ingest.py                 # Batch ingestion script (optional)
├── index.html                # Frontend dashboard
├── run.py                    # Legacy entry point
├── requirements.txt
├── .env                      # API keys (not tracked)
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Pinecone](https://www.pinecone.io/) account (free tier works)
- An [OpenAI](https://platform.openai.com/) API key

### 1. Clone the Repository

```bash
git clone https://github.com/koushik1359/RAG-Application.git
cd RAG-Application
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 5. Run the Server

```bash
python -m uvicorn app.main:app
```

### 6. Open the Dashboard

Open `index.html` in your browser. Upload documents using the sidebar or 📎 button.

---

## 📸 How It Works

1. **Upload** — Click the sidebar upload button or 📎 icon. Supports PDF, DOCX, TXT, CSV. The backend chunks it, embeds it, and stores it in Pinecone.
2. **Ask** — Type a specific question. The engine reformulates it using chat history, then searches Pinecone for the top 3 most relevant chunks.
3. **Answer** — GPT-3.5-Turbo generates a Markdown-formatted answer with exact source file and page citations.
4. **Manage** — View all uploaded documents in the sidebar. Delete individual files or clear the entire knowledge base.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
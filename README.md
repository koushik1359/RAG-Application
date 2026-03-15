# 🗄️ Enterprise RAG Engine — Chat With Your Documents

> An end-to-end Retrieval-Augmented Generation (RAG) application that lets you upload PDF documents, embed them into a cloud vector database, and ask natural-language questions — with **page-level source citations**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.3-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-VectorDB-purple)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--Turbo-412991?logo=openai)

---

## ✨ Features

| Feature | Description |
|---|---|
| **📄 PDF Upload via UI** | Upload any PDF directly from the browser — no terminal commands needed. |
| **🔍 Semantic Search** | Uses Hugging Face `all-MiniLM-L6-v2` embeddings to find the most relevant text chunks. |
| **🧠 AI-Powered Answers** | OpenAI GPT-3.5-Turbo reads the retrieved context and generates accurate answers. |
| **📑 Source Citations** | Every answer includes the exact **file name** and **page number** it came from. |
| **☁️ Cloud Vector Store** | Document embeddings are stored in Pinecone for fast, scalable similarity search. |
| **⚡ Real-Time Processing** | PDFs are chunked, embedded, and indexed on upload — ready to query instantly. |

---

## 🏗️ Architecture

```
┌──────────────┐     PDF Upload      ┌──────────────────┐
│   Frontend   │ ──────────────────► │  FastAPI Backend  │
│  (HTML/JS)   │                     │    /upload        │
└──────┬───────┘                     └────────┬─────────┘
       │                                      │
       │  User Question                       │ Chunk → Embed → Store
       │                                      ▼
       │                             ┌──────────────────┐
       │  POST /chat                 │     Pinecone      │
       └───────────────────────────► │  Vector Database   │
                                     └────────┬─────────┘
                                              │
                                              │ Top-K Similar Chunks
                                              ▼
                                     ┌──────────────────┐
                                     │   OpenAI GPT-3.5  │
                                     │   + RAG Context   │
                                     └──────────────────┘
                                              │
                                              │ Answer + Citations
                                              ▼
                                     ┌──────────────────┐
                                     │   Frontend Chat   │
                                     │   with Sources    │
                                     └──────────────────┘
```

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Orchestration:** LangChain
- **Vector Database:** Pinecone (Cloud)
- **Embeddings:** Hugging Face `all-MiniLM-L6-v2` (local, free)
- **LLM:** OpenAI GPT-3.5-Turbo
- **Frontend:** HTML, CSS, JavaScript (Dark Mode UI)

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
python -m uvicorn app:app
```

### 6. Open the Dashboard

Open `index.html` in your browser. Upload a PDF using the 📎 button and start asking questions!

---

## 📁 Project Structure

```
├── app.py              # FastAPI backend with /chat and /upload endpoints
├── ingest.py           # Batch ingestion script for bulk PDF processing
├── index.html          # Frontend chat dashboard (dark mode UI)
├── requirements.txt    # Python dependencies
├── .env                # API keys (not tracked by Git)
├── .gitignore          # Ignores venv, .env, documents, and cache
└── documents/          # Uploaded PDFs are stored here
```

---

## 📸 How It Works

1. **Upload** — Click the 📎 icon to upload a PDF. The backend chunks it, embeds it with Hugging Face, and stores it in Pinecone.
2. **Ask** — Type a specific question. The app converts it to a vector and searches Pinecone for the top 3 most relevant text chunks.
3. **Answer** — GPT-3.5-Turbo reads those chunks and generates a precise answer, citing the exact file and page number.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
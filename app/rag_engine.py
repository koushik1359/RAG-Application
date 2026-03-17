"""
rag_engine.py — Core RAG (Retrieval-Augmented Generation) pipeline.

Initializes all AI components:
  - HuggingFace Embeddings (bi-encoder for fast retrieval)
  - Cross-Encoder Re-Ranker (for precise relevance scoring)
  - Pinecone Vector Store
  - OpenAI LLM
  - History-Aware Retriever with Re-Ranking
  - RAG Chain

Architecture:
  Query → History Rewrite → Pinecone (top 10) → Cross-Encoder Re-Rank (top 3) → LLM → Answer
"""

import time
from pinecone import Pinecone
from sentence_transformers import CrossEncoder
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

from app.config import (
    PINECONE_API_KEY, INDEX_NAME, LLM_MODEL, 
    LLM_TEMPERATURE, EMBEDDING_MODEL, RETRIEVER_TOP_K,
    RERANKER_MODEL, RERANKER_TOP_K
)

# --- Initialize Pinecone Admin Client ---
print("Connecting to Pinecone Admin Client...")
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(INDEX_NAME)

# --- Initialize Embeddings (Bi-Encoder: fast, but approximate) ---
print("Loading Bi-Encoder Embeddings...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# --- Initialize Cross-Encoder Re-Ranker (slow, but precise) ---
print("Loading Cross-Encoder Re-Ranker...")
reranker = CrossEncoder(RERANKER_MODEL)
print(f"Re-Ranker loaded: {RERANKER_MODEL}")

# --- Initialize Vector Store & Retriever ---
print("Connecting to Pinecone Vector Store...")
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
# Retrieve MORE chunks than needed — the re-ranker will filter down
base_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})

# --- Initialize LLM ---
print("Loading OpenAI LLM...")
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)


# --- Custom Re-Ranking Retriever ---
def rerank_documents(query: str, documents: list[Document]) -> list[Document]:
    """
    Re-rank retrieved documents using a Cross-Encoder.
    
    Bi-encoders (used by Pinecone) encode query and document SEPARATELY.
    Cross-encoders encode them TOGETHER, which is slower but far more accurate.
    
    Pipeline: Pinecone returns top 10 → Cross-Encoder scores each → Keep top 3
    """
    if not documents:
        return documents
    
    start = time.time()
    
    # Create (query, document) pairs for the cross-encoder
    pairs = [(query, doc.page_content) for doc in documents]
    
    # Score each pair — higher = more relevant
    scores = reranker.predict(pairs)
    
    # Attach scores and sort
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    # Keep only the top RERANKER_TOP_K
    reranked = [doc for doc, score in scored_docs[:RERANKER_TOP_K]]
    
    elapsed = round((time.time() - start) * 1000, 1)
    print(f"  Re-Ranker: scored {len(documents)} docs → kept top {RERANKER_TOP_K} ({elapsed}ms)")
    
    # Log the score distribution for debugging
    for doc, score in scored_docs[:RERANKER_TOP_K]:
        source = doc.metadata.get("source", "?")
        print(f"    ✅ {score:.3f} — {source}")
    for doc, score in scored_docs[RERANKER_TOP_K:]:
        source = doc.metadata.get("source", "?")
        print(f"    ❌ {score:.3f} — {source}")
    
    return reranked


# --- Build Conversational RAG Chain ---

# Step 1: History-Aware Retriever
# Reformulates the user's question using chat history before searching
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Given a chat history and the latest user question which might reference context in the chat history, "
     "formulate a standalone question which can be understood without the chat history. "
     "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(llm, base_retriever, contextualize_prompt)

# Step 2: Answer Generation Prompt
system_prompt = (
    "You are a helpful and intelligent AI assistant for an enterprise company. "
    "Use the following pieces of retrieved context to answer the user's question. "
    "If you don't know the answer based on the context, just say that you don't know. "
    "ALWAYS cite your sources by mentioning the file name and page number found in the metadata. "
    "\n\n"
    "Context: {context}"
)

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Step 3: Combine into final chain
question_answer_chain = create_stuff_documents_chain(llm, answer_prompt)


def run_rag_pipeline(query: str, chat_history: list) -> dict:
    """
    Full RAG pipeline with re-ranking and performance logging.
    
    Returns:
        dict with 'answer', 'context' (re-ranked docs), and 'performance' timings
    """
    performance = {}
    
    # Step 1: Retrieve top-K from Pinecone (via history-aware retriever)
    t0 = time.time()
    retrieved_docs = history_aware_retriever.invoke({
        "input": query,
        "chat_history": chat_history
    })
    performance["retrieval_ms"] = round((time.time() - t0) * 1000, 1)
    print(f"  Retrieval: {len(retrieved_docs)} docs ({performance['retrieval_ms']}ms)")
    
    # Step 2: Re-rank with Cross-Encoder
    t1 = time.time()
    reranked_docs = rerank_documents(query, retrieved_docs)
    performance["reranking_ms"] = round((time.time() - t1) * 1000, 1)
    
    # Step 3: Generate answer with LLM
    t2 = time.time()
    answer = question_answer_chain.invoke({
        "input": query,
        "chat_history": chat_history,
        "context": reranked_docs
    })
    performance["llm_ms"] = round((time.time() - t2) * 1000, 1)
    print(f"  LLM: generated answer ({performance['llm_ms']}ms)")
    
    performance["total_ms"] = round((time.time() - t0) * 1000, 1)
    print(f"  Total pipeline: {performance['total_ms']}ms")
    
    return {
        "answer": answer,
        "context": reranked_docs,
        "performance": performance
    }


print("RAG Engine initialized successfully! (with Cross-Encoder Re-Ranking)")

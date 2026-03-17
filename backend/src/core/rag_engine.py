"""
backend/src/core/rag_engine.py — Core RAG pipeline.

Streaming Support Added:
  - astream_pipeline yields token-by-token
  - Encapsulates metadata (sources, performance) in the first chunk
"""

import time
import logging
import json
from pinecone import Pinecone
from sentence_transformers import CrossEncoder
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

from backend.src.config import (
    PINECONE_API_KEY, INDEX_NAME, LLM_MODEL, 
    LLM_TEMPERATURE, EMBEDDING_MODEL, RETRIEVER_TOP_K,
    RERANKER_MODEL, RERANKER_TOP_K
)

logger = logging.getLogger("uvicorn.error")

class RAGEngine:
    def __init__(self):
        logger.info("Initializing RAGEngine components...")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.pinecone_index = self.pc.Index(INDEX_NAME)
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.reranker = CrossEncoder(RERANKER_MODEL)
        self.vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=self.embeddings)
        self.base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, streaming=True)
        self._init_chains()
        logger.info(f"RAGEngine initialized with Streaming Support")

    def _init_chains(self):
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Formulate a standalone question from history and input."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        self.history_aware_retriever_chain = create_history_aware_retriever(
            self.llm, self.base_retriever, contextualize_prompt
        )

        system_prompt = (
            "You are a helpful and intelligent AI assistant. "
            "Use the context to answer. If unknown, say so. "
            "Cite sources (filename, page).\n\nContext: {context}"
        )
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        self.question_answer_chain = create_stuff_documents_chain(self.llm, answer_prompt)

    async def rerank_documents(self, query: str, documents: list[Document]) -> list[Document]:
        if not documents: return documents
        start = time.time()
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.reranker.predict(pairs)
        scored_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        reranked = [doc for doc, score in scored_docs[:RERANKER_TOP_K]]
        logger.info(f"Re-Ranker: {len(documents)} -> {len(reranked)} ({round((time.time()-start)*1000)}ms)")
        return reranked

    async def astream_pipeline(self, query: str, chat_history: list):
        """
        Streaming generator for RAG pipeline.
        Yields:
          1. Metadata Chunk (JSON string with "type": "metadata")
          2. Content Chunks (plain text tokens)
        """
        performance = {}
        t0 = time.time()

        # 1. Retrieval
        retrieved_docs = await self.history_aware_retriever_chain.ainvoke({
            "input": query, "chat_history": chat_history
        })
        performance["retrieval_ms"] = round((time.time() - t0) * 1000, 1)

        # 2. Re-Ranking
        t1 = time.time()
        reranked_docs = await self.rerank_documents(query, retrieved_docs)
        performance["reranking_ms"] = round((time.time() - t1) * 1000, 1)

        # Format sources for metadata chunk
        sources = []
        for doc in reranked_docs:
            sources.append({
                "source": doc.metadata.get("source", "Unknown").split('/')[-1],
                "page": doc.metadata.get("page", "Unknown"),
                "content": doc.page_content[:200] + "..."
            })

        # Yield Initial Metadata (Hidden from user text, used by frontend to update UI state)
        # We wrap in a specific format so frontend can detect it
        metadata = {
            "type": "metadata",
            "sources": sources,
            "performance": performance # Initial perfs
        }
        yield json.dumps(metadata) + "|||" # Separator

        # 3. Streaming Generation
        t2 = time.time()
        # total_ms will be updated at the end, but we send what we have
        
        async for chunk in self.question_answer_chain.astream({
            "input": query,
            "chat_history": chat_history,
            "context": reranked_docs
        }):
            yield chunk

        # Final Performance log
        total_time = round((time.time() - t0) * 1000, 1)
        llm_time = round((time.time() - t2) * 1000, 1)
        
        final_metadata = {
            "type": "final_metadata",
            "performance": {
                "llm_ms": llm_time,
                "total_ms": total_time
            }
        }
        yield "|||" + json.dumps(final_metadata)
        logger.info(f"Streaming complete in {total_time}ms")
    async def run_pipeline(self, query: str, chat_history: list) -> dict:
        """Non-streaming version for evaluation and testing."""
        performance = {}
        t0 = time.time()

        retrieved_docs = await self.history_aware_retriever_chain.ainvoke({
            "input": query, "chat_history": chat_history
        })
        performance["retrieval_ms"] = round((time.time() - t0) * 1000, 1)

        t1 = time.time()
        reranked_docs = await self.rerank_documents(query, retrieved_docs)
        performance["reranking_ms"] = round((time.time() - t1) * 1000, 1)

        t2 = time.time()
        answer = await self.question_answer_chain.ainvoke({
            "input": query,
            "chat_history": chat_history,
            "context": reranked_docs
        })
        performance["llm_ms"] = round((time.time() - t2) * 1000, 1)
        performance["total_ms"] = round((time.time() - t0) * 1000, 1)

        return {
            "answer": answer,
            "context": reranked_docs,
            "performance": performance
        }

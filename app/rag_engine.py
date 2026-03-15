"""
rag_engine.py — Core RAG (Retrieval-Augmented Generation) pipeline.

Initializes all AI components:
  - HuggingFace Embeddings
  - Pinecone Vector Store
  - OpenAI LLM
  - History-Aware Retriever
  - RAG Chain

Other modules import from here instead of initializing their own instances.
"""

from pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config import (
    PINECONE_API_KEY, INDEX_NAME, LLM_MODEL, 
    LLM_TEMPERATURE, EMBEDDING_MODEL, RETRIEVER_TOP_K
)

# --- Initialize Pinecone Admin Client ---
print("Connecting to Pinecone Admin Client...")
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(INDEX_NAME)

# --- Initialize Embeddings ---
print("Loading Embeddings...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# --- Initialize Vector Store & Retriever ---
print("Connecting to Pinecone Vector Store...")
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})

# --- Initialize LLM ---
print("Loading OpenAI LLM...")
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

# --- Build Conversational RAG Chain ---

# Step 1: History-Aware Retriever
# Reformulates the user's question using chat history before searching
# e.g., "What are his skills?" → "What are Koushik's skills?"
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Given a chat history and the latest user question which might reference context in the chat history, "
     "formulate a standalone question which can be understood without the chat history. "
     "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)

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

# Step 3: Combine into final RAG chain
question_answer_chain = create_stuff_documents_chain(llm, answer_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

print("RAG Engine initialized successfully!")

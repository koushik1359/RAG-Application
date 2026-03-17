import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

# Load shared config
from backend.src.config import PINECONE_API_KEY, INDEX_NAME, DOCUMENTS_DIR, EMBEDDING_MODEL

load_dotenv()

def main():
    print("1. Connecting to Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)

    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        while not pc.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)
    
    print("\n2. Loading documents...")
    loader = PyPDFDirectoryLoader(DOCUMENTS_DIR)
    raw_documents = loader.load()
    
    if not raw_documents:
        print(f"No PDFs found in {DOCUMENTS_DIR}")
        return

    print("\n3. Chunking...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = text_splitter.split_documents(raw_documents)

    print("\n4. Embedding & Uploading...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    PineconeVectorStore.from_documents(
        documents=documents, 
        embedding=embeddings, 
        index_name=INDEX_NAME
    )
    
    print("\n✅ Ingestion Complete.")

if __name__ == "__main__":
    main()

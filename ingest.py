import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import time

# Load API keys from the .env file
load_dotenv()

# We need an Index Name for Pinecone
INDEX_NAME = "enterprise-rag"

def main():
    print("1. Loading API Keys...")
    pc_api_key = os.getenv("PINECONE_API_KEY")
    if not pc_api_key:
        raise ValueError("PINECONE_API_KEY is not set in the .env file")

    print("2. Connecting to Pinecone...")
    pc = Pinecone(api_key=pc_api_key)

    # Check if index exists, if not, create it
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating Pinecone index '{INDEX_NAME}'... This may take a minute.")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384, # The exact dimension size for 'all-MiniLM-L6-v2' model
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1" # Make sure this matches your free tier Pinecone region
            )
        )
        # Wait a moment for Pinecone to initialize the new index
        while not pc.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)
    
    print("Pinecone index is ready!")

    print("\n3. Loading PDFs from the 'documents' folder...")
    # This looks for a folder named "documents" in the same directory
    loader = PyPDFDirectoryLoader("./documents")
    raw_documents = loader.load()
    
    if not raw_documents:
        print("ERROR: No PDFs found! Did you create a 'documents' folder and put a PDF inside it?")
        return

    print(f"Loaded {len(raw_documents)} pages across your documents.")

    print("\n4. Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    documents = text_splitter.split_documents(raw_documents)
    print(f"Split documents into {len(documents)} chunks.")

    print("\n5. Loading embedding model (Hugging Face MiniLM)...")
    # This downloads the open-source embedding model the first time it runs
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("\n6. Embedding chunks and uploading to Pinecone...")
    PineconeVectorStore.from_documents(
        documents=documents, 
        embedding=embeddings, 
        index_name=INDEX_NAME
    )
    
    print("\n✅ SUCCESS! All documents have been embedded and stored in Pinecone.")

if __name__ == "__main__":
    main()

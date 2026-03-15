import os
import shutil
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

app = FastAPI(title="Enterprise RAG API")

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI components once when the server starts
INDEX_NAME = "enterprise-rag"

print("Loading Embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("Connecting to Pinecone Vector Store...")
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
# Create a retriever that fetches the top 3 most relevant chunks
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

print("Loading OpenAI LLM...")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define how the AI should answer
system_prompt = (
    "You are a helpful and intelligent AI assistant for an enterprise company. "
    "Use the following pieces of retrieved context to answer the user's question. "
    "If you don't know the answer based on the context, just say that you don't know. "
    "ALWAYS cite your sources by mentioning the file name and page number found in the metadata. "
    "\n\n"
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Combine the retrieval step and the LLM generation step
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


# Define what the API expects to receive
class ChatRequest(BaseModel):
    message: str

# Define the API Route for uploading
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    print(f"Receiving file: {file.filename}")
    
    # Save the file to the documents folder
    os.makedirs("documents", exist_ok=True)
    file_path = os.path.join("documents", file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    print(f"File saved to {file_path}. Processing...")
    
    try:
        # Load and process the single PDF
        loader = PyPDFLoader(file_path)
        raw_documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        documents = text_splitter.split_documents(raw_documents)
        
        print(f"Split {file.filename} into {len(documents)} chunks. Uploading to Pinecone...")
        
        # Embed and upload to Pinecone
        vectorstore.add_documents(documents)
        
        return {
            "success": True, 
            "message": f"Successfully processed {file.filename} and added {len(documents)} chunks to the RAG Engine."
        }
    except Exception as e:
        print(f"Error processing upload: {e}")
        return {
            "success": False,
            "message": str(e)
        }

# Define the API Route
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"Received question: {request.message}")
    
    # Run the RAG pipeline
    response = rag_chain.invoke({"input": request.message})
    
    # Extract the sources so we can send them to the frontend
    sources = []
    for doc in response["context"]:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        sources.append({"source": source, "page": page, "content": doc.page_content})
        
    return {
        "answer": response["answer"],
        "sources": sources
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

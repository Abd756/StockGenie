from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# File paths
pdf_path = "stockgenie.pdf"
text_path = "stockgenie_knowledge.txt"

# Load PDF document
# print(f"Loading PDF: {pdf_path}")
# pdf_loader = PyPDFLoader(pdf_path)
# pdf_docs = pdf_loader.load()

# Load text document
print(f"Loading text: {text_path}")
text_loader = TextLoader(text_path)
text_docs = text_loader.load()

# Combine all documents
all_docs =  text_docs
print(f"Total documents loaded: {len(all_docs)}")

# Split documents into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
doc_chunks = splitter.split_documents(all_docs)
print(f"Total chunks after splitting: {len(doc_chunks)}")

# Initialize embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create vector store (overwrite existing)
vectorstore = Chroma.from_documents(
    documents=doc_chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("Embeddings created and stored in ChromaDB successfully.")

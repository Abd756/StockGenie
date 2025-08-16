from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize embedding model (same as used for document ingestion)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Load the existing vector store
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# Create a retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Initialize the chat model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

# Create memory for conversation history
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# Custom prompt template for conversational retrieval
prompt_template = """
You are a helpful assistant that answers questions based on the provided context from the document and conversation history.
Use the following pieces of context to answer the question. Consider the chat history for context.
If you don't know the answer based on the context, just say that you don't know.

Context from document:
{context}

Chat History:
{chat_history}

Current Question: {question}

Answer:
"""
PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "chat_history", "question"]
)

# Create the ConversationalRetrievalChain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
    combine_docs_chain_kwargs={"prompt": PROMPT}
)

def get_chatbot_response(question: str) -> dict:
    """
    Get chatbot response for a given question using the conversational retrieval chain.
    Returns answer and source documents.
    """
    result = qa_chain({"question": question})
    return {
        "answer": result["answer"],
        "sources": [doc.page_content for doc in result["source_documents"]],
        "chat_history": memory.chat_memory.messages
    }
    
    
if __name__ == "__main__":
        print("Invest Genie Chatbot Test Console")
        print("Type your question and press Enter. Type 'quit' to exit.\n")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Goodbye!")
                break
            response = get_chatbot_response(user_input)
            print(f"\nBot: {response['answer']}")
            print(f"Sources used: {len(response['sources'])}")
            print("-" * 40)

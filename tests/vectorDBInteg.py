from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA

# Load embeddings
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Load FAISS index
db = FAISS.load_local(
    "securefill_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Optimized retriever with MMR
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,          # Number of documents to retrieve
        "fetch_k": 10    # Number of candidates to consider for diversity
    }
)

# Load Ollama LLM
# llm = OllamaLLM(model="phi3:mini", temperature=0.5)
llm = OllamaLLM(model="gemma2:2b", temperature=0.5)


# Create RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Ask question
query = "what is my credit card number?"
response = qa_chain.invoke({"query": query})

# Print answer
print("Answer:", response["result"])

# Print retrieved documents
print("\nRetrieved Documents:")
for i, doc in enumerate(response["source_documents"]):
    print(f"Document {i+1}: {doc.page_content}")

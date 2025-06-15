from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# --- Setup LangChain Components ---
DB_PATH = "./DataStore/faiss_index"
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load or create FAISS index
try:
    vectorstore = FAISS.load_local(DB_PATH, embedding_function, allow_dangerous_deserialization=True)
    print(f"✅ Loaded existing FAISS index from: {DB_PATH}")
except Exception:
    vectorstore = FAISS.from_texts(["dummy"], embedding_function)
    vectorstore.save_local(DB_PATH)
    print(f"✅ Created new FAISS index at: {DB_PATH}")


# --- Add Document Function Only ---
def add_document(attribute: str, value: str, metadata: str) -> None:
    """Add a plain text document to the FAISS index with rich context."""
    plain_text = f"Field: {attribute} | Value: {value} | Description: {metadata}"
    vectorstore.add_texts([plain_text])
    vectorstore.save_local(DB_PATH)

    print(f"✓ Document added: {plain_text}")

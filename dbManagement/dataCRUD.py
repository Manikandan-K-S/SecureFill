import uuid
import json
from langchain_huggingface import HuggingFaceEmbeddings  # ✅ Updated import
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

# --- 1. Setup LangChain Components ---
DB_PATH = "./DataStore"
COLLECTION_NAME = "document_store_lc"

# Initialize embedding function and Chroma vector store
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_function,
    persist_directory=DB_PATH,
)

print(f"✅ Chroma vector store initialized: '{COLLECTION_NAME}'")

# --- 2. Define CRUD & Search Functions ---

def add_document(attribute: str, value: str, metadata: str) -> str:
    """Add a document with proper embedding including the value."""
    doc_id = str(uuid.uuid4())
    embedding_text = f"Attribute: {attribute}. Metadata: {metadata}. Value: {value}"
    doc = Document(
        page_content=embedding_text,
        metadata={"sensitive_value": value, "description": metadata},
    )
    vectorstore.add_documents([doc], ids=[doc_id])
    print(f"✓ Document added with ID: {doc_id}")
    return doc_id

def delete_document(doc_id: str) -> None:
    """Delete a document by its ID."""
    try:
        vectorstore.delete(ids=[doc_id])
        print(f"✓ Document with ID '{doc_id}' has been deleted.")
    except Exception as e:
        print(f"⚠️ Error deleting document with ID '{doc_id}': {e}")

def update_document(doc_id: str, attribute: str, value: str, metadata: str) -> None:
    """Update an existing document by replacing content at the same ID."""
    delete_document(doc_id)
    embedding_text = f"Attribute: {attribute}. Metadata: {metadata}. Value: {value}"
    doc = Document(
        page_content=embedding_text,
        metadata={"sensitive_value": value, "description": metadata},
    )
    vectorstore.add_documents([doc], ids=[doc_id])
    print(f"✓ Document with ID '{doc_id}' has been updated.")

def view_all() -> list[dict]:
    """Retrieve all documents: returns a list of dicts with id, value, metadata."""
    results = vectorstore._collection.get(include=["metadatas", "documents"])
    output = []
    for i, _id in enumerate(results.get("ids", [])):
        md = results["metadatas"][i]
        output.append({
            "id": _id,
            "value": md.get("sensitive_value"),
            "metadata": md.get("description")
        })
    return output

def view_document(doc_id: str) -> dict | None:
    """Fetch a specific document by ID."""
    result = vectorstore._collection.get(ids=[doc_id], include=["metadatas", "documents"])
    if not result.get("ids"):
        return None
    md = result["metadatas"][0]
    return {"id": result["ids"][0], "value": md.get("sensitive_value"), "metadata": md.get("description")}

def similarity_search(query: str, top_k: int = 4) -> list[dict]:
    """Find top-k documents similar to query."""
    results = vectorstore.similarity_search(query, k=top_k)
    return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]

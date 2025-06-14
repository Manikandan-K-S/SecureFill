import uuid
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

# --- 1. Setup LangChain Components ---
DB_PATH = "./DataStore"
COLLECTION_NAME = "document_store_lc"

# Initialize the embedding function and the Chroma vector store
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_function,
    persist_directory=DB_PATH
)

print(f"✅ LangChain Chroma vector store initialized. Using collection '{COLLECTION_NAME}'.")

# --- 2. Define CRUD Functions ---

def add_document(attribute: str, value: str, metadata: str):
    """
    Adds a new document with a randomly generated ID using LangChain.

    Args:
        attribute (str): The descriptive attribute for the document.
        value (str): The actual content/value of the document.
        metadata (str): A flat text string of metadata.

    Returns:
        str: The randomly generated ID of the newly added document.
    """
    doc_id = str(uuid.uuid4())
    # In LangChain, the rich text for embedding is the 'page_content'.
    # The actual value is stored in the metadata for retrieval.
    embedding_text = f"Attribute: {attribute}. Metadata: {metadata}"
    
    doc = Document(
        page_content=embedding_text,
        metadata={"sensitive_value": value, "description": metadata}
    )
    
    vectorstore.add_documents([doc], ids=[doc_id])
    print(f"✓ Document added with ID: {doc_id}")
    return doc_id

def delete_document(doc_id: str):
    """
    Deletes a document with the given ID using LangChain.

    Args:
        doc_id (str): The ID of the document to delete.
    """
    try:
        vectorstore.delete(ids=[doc_id])
        print(f"✓ Document with ID '{doc_id}' has been deleted.")
    except Exception as e:
        print(f"⚠️ Error deleting document with ID '{doc_id}': {e}")

def update_document(doc_id: str, attribute: str, value: str, metadata: str):
    """
    Updates a document by deleting the old one and adding a new one with the same ID.

    Args:
        doc_id (str): The ID of the document to update.
        attribute (str): The new descriptive attribute.
        value (str): The new content/value.
        metadata (str): The new flat text metadata.
    """
    # LangChain's common update pattern is delete then add.
    delete_document(doc_id)
    
    embedding_text = f"Attribute: {attribute}. Metadata: {metadata}"
    doc = Document(
        page_content=embedding_text,
        metadata={"sensitive_value": value, "description": metadata}
    )
    
    vectorstore.add_documents([doc], ids=[doc_id])
    print(f"✓ Document with ID '{doc_id}' has been updated.")

def view_all():
    """
    Retrieves all documents from the collection.
    Note: Accesses the underlying native Chroma collection for this operation.

    Returns:
        list: A list of dictionaries, where each dictionary represents a document.
    """
    # LangChain's standard interface doesn't have a 'view_all'.
    # We access the underlying Chroma client's method.
    results = vectorstore._collection.get(include=["metadatas", "documents"])
    
    if not results['ids']:
        return []

    all_docs = []
    for i in range(len(results['ids'])):
        doc = {
            "id": results['ids'][i],
            # Reconstruct what was stored from LangChain's perspective
            "value": results['metadatas'][i].get('sensitive_value'),
            "metadata": results['metadatas'][i].get('description')
        }
        all_docs.append(doc)
        
    return all_docs

def view_document(doc_id: str):
    """
    Fetches the details of a document with the given ID.
    Note: Accesses the underlying native Chroma collection for this operation.

    Args:
        doc_id (str): The ID of the document to retrieve.

    Returns:
        dict: A dictionary representing the document, or None if not found.
    """
    result = vectorstore._collection.get(ids=[doc_id], include=["metadatas", "documents"])
    
    if not result['ids']:
        return None
        
    doc = {
        "id": result['ids'][0],
        "value": result['metadatas'][0].get('sensitive_value'),
        "metadata": result['metadatas'][0].get('description')
    }
    return doc

def similarity_search(query: str, top_k: int = 4):
    """
    Performs a similarity search in the vector database using the provided query text.

    Args:
        query (str): The text input to search similar documents for.
        top_k (int): Number of similar documents to retrieve.

    Returns:
        list: A list of dictionaries representing the similar documents.
    """
    results = vectorstore.similarity_search(query, k=top_k)

    similar_docs = []
    for doc in results:
        similar_docs.append({
            "content": doc.page_content,
            "metadata": doc.metadata
        })

    print(f"✓ Found {len(similar_docs)} similar documents for query: '{query}'")
    return similar_docs



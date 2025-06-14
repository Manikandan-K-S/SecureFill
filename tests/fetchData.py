import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document

# --- 1. Configuration: Point to your existing database ---
DB_PATH = "./DataStore"
COLLECTION_NAME = "document_store_lc"



def query_database(query_text: str, vectorstore, k: int = 3):
    """
    Performs a similarity search on the vector store.

    Args:
        query_text (str): The natural language query to search for.
        vectorstore: The initialized LangChain Chroma vector store object.
        k (int): The number of top results to return.

    Returns:
        list: A list of LangChain Document objects that are most similar to the query.
    """
    print(f"\n🔎 Performing similarity search for: '{query_text}'")
    try:
        results = vectorstore.similarity_search(query_text, k=k)
        return results
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return []

# --- Main Execution ---
if __name__ == "__main__":
    # Check if the database path exists
    if not os.path.exists(DB_PATH):
        print(f"Error: Database path '{DB_PATH}' not found.")
        print("Please ensure you have created the database first or correct the path.")
    else:
        # Initialize the embedding function
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        # Load the existing vector store from disk
        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_function,
            persist_directory=DB_PATH
        )
        
        print(f"✅ Successfully loaded vector store from '{DB_PATH}'.")

        # Run setup to add data only if needed

        # --- Perform a query ---
        my_query = "What is the primary email for the user?"
        search_results = query_database(my_query, vectorstore)

        if search_results:
            print("\n--- Search Results ---")
            for i, doc in enumerate(search_results):
                print(f"\nResult {i+1}:")
                # The 'page_content' is the text that was used for the embedding/search
                print(f"  Page Content (for matching): {doc.page_content}")
                # The actual value is stored in the metadata
                print(f"  Metadata (contains actual value): {doc.metadata}")
                retrieved_value = doc.metadata.get('sensitive_value', 'N/A')
                print(f"  >> Retrieved Value: {retrieved_value}")
        else:
            print("\n--- No results found. ---")

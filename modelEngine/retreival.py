import yaml
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from modelWrapper import CustomHTTPChatModel

# Load API config
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Create LLM instance
llm = CustomHTTPChatModel(
    api_key=config["api_key"],
    base_url=config["model_server_base_url"],
    workspace_slug=config["workspace_slug"]
)

# Setup vector store
embedding_fn = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name="document_store_lc",
    embedding_function=embedding_fn,
    persist_directory="./DataStore"
)

retriever = vectorstore.as_retriever()

# Setup RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Run interactive query
if __name__ == "__main__":
    q = input("Enter query: ")
    resp = qa_chain.invoke({"query": q})
    print("\nAnswer:", resp["result"])
    print("\nSources:")
    for doc in resp["source_documents"]:
        print("-", doc.page_content)

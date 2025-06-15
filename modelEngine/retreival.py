import yaml
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from modelWrapper import CustomHTTPChatModel

# --- Load API Config ---
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# --- Create LLM Instance ---
llm = CustomHTTPChatModel(
    api_key=config["api_key"],
    base_url=config["model_server_base_url"],
    workspace_slug=config["workspace_slug"]
)

# --- Setup Vector Store ---
embedding_fn = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name="document_store_lc",
    embedding_function=embedding_fn,
    persist_directory="./DataStore"
)

retriever = vectorstore.as_retriever()

# --- Custom Prompt Template ---
custom_prompt = PromptTemplate.from_template(
    """You are a smart form filler. You must strictly use only the information provided in the context below.

If the answer is not found in the context, you must say "Data not found" and return this JSON:
{{"field": "Aadhar Number", "value": null}}

If the answer is found, return this JSON:
{{"field": "Aadhar Number", "value": "<retrieved value>"}}

Context:
{context}

Question:
{question}
"""
)

# --- Setup RetrievalQA Chain ---
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": custom_prompt}
)

# --- Run Interactive Query ---
if __name__ == "__main__":
    q = "What is the Aadhar number?"
    resp = qa_chain.invoke({"query": q})

    print("\nAnswer:", resp["result"])
    print("\nSources:")
    for doc in resp["source_documents"]:
        print("-", doc.page_content)

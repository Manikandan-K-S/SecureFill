'''
This script demonstrates how to use LangChain with Ollama and FAISS for vector database integration.
It uses the BGE embeddings model from HuggingFace and the Ollama LLM to create a RetrievalQA chain.

Make sure you have the following prerequisites installed:

    Install the required packages:
    pip install langchain langchain-community langchain-huggingface langchain-ollama faiss-cpu

    Install Ollama and the Gemma2 model:
    ollama pull gemma2:2b
'''

import time
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

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
llm = OllamaLLM(model="gemma2:2b", temperature=0.5)

# Create RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Define the PromptTemplate
query_template = """
You are a personal data retrieval assistant.

Retrieve the user's personal information from the provided documents.

Respond strictly in this JSON format:
Query: "{query}"
"""

prompt = PromptTemplate(
    input_variables=["query"],
    template=query_template
)

input_query = "What is my email address?"

query = prompt.format(query=input_query)

start = time.time()
response = qa_chain.invoke({"query": query})
end = time.time()

    # Print execution time
print(f"\nExecution Time: {end - start:.2f} seconds")

    # Print answer
print(f"Answer for '{query}': {response['result']}")

    # Print retrieved documents
print("\nRetrieved Documents:")

for i, doc in enumerate(response["source_documents"]):
    print(f"Document {i+1}: {doc.page_content}")


'''
This script demonstrates how to use LangChain with Ollama and FAISS for vector database integration.
It uses the BGE embeddings model from HuggingFace and the Ollama LLM to create a RetrievalQA chain.

Prerequisites:
    pip install langchain langchain-community langchain-huggingface langchain-ollama faiss-cpu
    ollama pull gemma2:2b
'''

import time
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

start = time.time()
# Load embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")

# Load FAISS index
db = FAISS.load_local(
    "securefill_index",
    embeddings,
    allow_dangerous_deserialization=True
)

end = time.time()
# Optimized retriever with MMR
print(f"FAISS index loaded in {end - start:.2f} seconds")
start = time.time()
retriever = db.as_retriever(search_kwargs={"k": 10})
end = time.time()

print(f"FAISS retreiver time {end - start:.2f} seconds")

# Load Ollama LLM
start = time.time()
llm = OllamaLLM(model="granite3.3:2b", temperature=0.5)
end = time.time()
print(f"Ollama LLM loaded in {end - start:.2f} seconds")
# Create RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Define the PromptTemplate
query_template = """
You are a personal data retrieval assistant.

From the provided documents, retrieve the user's personal information which is asked donot provide extra content.

Your response must be strictly in this JSON format for each mentioned key:
{{
    "key - attribute": "<the answer or 'Data not found' if the information is missing>"
}}

Query: "{query}"
"""

prompt = PromptTemplate(
    input_variables=["query"],
    template=query_template
)

# User Query
input_query = "pan card no"
query = prompt.format(query=input_query)

for i in range(4):
    print(f"\nIteration {i + 1}:")
    # Measure execution time
    start = time.time()
    response = qa_chain.invoke({"query": query})
    end = time.time()

    # Display results
    print(f"\nExecution Time: {end - start:.2f} seconds")
    print(f"\nAnswer:\n{response['result']}")

print("\nRetrieved Documents:")
for i, doc in enumerate(response["source_documents"]):
    print(f"Document {i + 1}: {doc.page_content}")

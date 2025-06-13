'''
This script demonstrates how to use LangChain with Ollama and FAISS for vector database integration.
It uses the BGE embeddings model from HuggingFace and the Phi4 model from Ollama to create a RetrievalQA chain.


Make sure you have the following prerequisites installed:

    Install the required packages:
    pip install langchain langchain-community langchain-huggingface langchain-ollama faiss-cpu

    Install Ollama and the Phi4 model:
    ollama pull phi4-mini:3.8b

'''


from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA

# 1. Create embeddings using bge-small-en
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# 2. Create FAISS vector store
db = FAISS.from_texts([
    "12344 is my Canara Bank account number.",
    "I have an account with Canara Bank in Thindal.",
    "The card number associated with my account is 1234 5678 9012 3456.",
    "SecureFill is activated via a keyboard shortcut and performs all operations on the user's device for maximum privacy.",
    "SecureFill can be useful for users who want faster form filling without compromising their personal data privacy."
], embedding=embeddings)

retriever = db.as_retriever()

# 3. Initialize LLM from Ollama
llm = OllamaLLM(model="phi4-mini:3.8b", temperature=0.5)

# 4. Create RetrievalQA chain with source documents returned
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# 5. Ask question
query = "what is my bank acc number return response as json"
response = qa_chain.invoke({"query": query})

# Print the answer
print("Answer:", response["result"])

# Print the retrieved documents
print("\nRetrieved Documents:")
for i, doc in enumerate(response["source_documents"]):
    print(f"Document {i+1}: {doc.page_content}")

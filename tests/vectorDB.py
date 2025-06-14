from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Prepare the texts
texts = [
    # Personal Information
    "My name is John Doe.",
    "My email address is john.doe@example.com.",
    "My phone number is +1 234 567 8901.",
    "My date of birth is January 1, 1990.",
    # Address Information
    "My home address is 123 Main Street, Springfield.",
    "I live in apartment number 45B, Maple Residency.",
    "My postal code is 123456.",
    # Financial Information
    "My Canara Bank account number is 1234567890.",
    "I have a savings account with Canara Bank at the Thindal branch.",
    "My debit card number is 1234 5678 9012 3456.",
    "My credit card number is 9876 5432 1098 7654.",
    "My PAN card number is ABCDE1234F.",
    "My UPI ID is john.doe@upi.",
    "aadhar number is 12234234",
    # SecureFill Context
    "SecureFill is activated via a keyboard shortcut.",
    "SecureFill performs all operations on the user's device to ensure maximum privacy.",
    "SecureFill automatically fills forms using stored personal information.",
    "SecureFill helps users complete forms quickly without sending data to the cloud.",
    "SecureFill can be useful for users who want faster form filling without compromising their personal data privacy.",
    "SecureFill supports multiple profiles, allowing users to switch between personal and work information.",
    # Additional User Scenarios
    "my home address is dsfdsf dfdfsjn",
    "My work email is john.doe@company.com.",
    "My company address is 789 Corporate Plaza, New York.",
    "My work phone number is +1 987 654 3210.",
    "My secondary contact number is +1 555 555 5555.",
    "My alternate address is 456 Side Street, Hillview Town.",
    # Dummy Financial Samples
    "My ICICI Bank account number is 5566778899.",
    "My HDFC credit card number is 1122 3344 5566 7788.",
    "My UPI ID for work is john.work@upi."
]

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2")

# Create FAISS vector store (no index_factory)
db = FAISS.from_texts(
    texts,
    embedding=embeddings
)

# Save the FAISS index
db.save_local("securefill_index")

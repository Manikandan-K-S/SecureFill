# sample.py

from dataCRUD import add_document, delete_document, update_document, view_all, view_document, similarity_search

# --- 1. Add Documents ---
print("\n--- Adding Documents ---")
doc_id1 = add_document("Name", "John Doe", "Personal data")
doc_id2 = add_document("Email", "john.doe@example.com", "Personal data")
doc_id3 = add_document("Phone", "+1234567890", "Personal data")

# --- 2. View All Documents ---
print("\n--- Viewing All Documents ---")
all_docs = view_all()
for doc in all_docs:
    print(doc)

# --- 3. View a Specific Document ---
print("\n--- Viewing Specific Document ---")
viewed_doc = view_document(doc_id2)
print(viewed_doc)

# --- 4. Update a Document ---
print("\n--- Updating Document ---")
update_document(doc_id3, "Phone", "+0987654321", "Updated contact number")

# View the updated document
updated_doc = view_document(doc_id3)
print(updated_doc)

# --- 5. Perform Similarity Search ---
print("\n--- Similarity Search ---")
query = "Find contact details"
similar_docs = similarity_search(query, top_k=2)
for doc in similar_docs:
    print(doc)

# --- 6. Delete a Document ---
print("\n--- Deleting Document ---")
delete_document(doc_id1)

# --- 7. View All Documents After Deletion ---
print("\n--- Viewing All Documents After Deletion ---")
all_docs_after_deletion = view_all()
for doc in all_docs_after_deletion:
    print(doc)

print("\n✅ Sample operations completed.")

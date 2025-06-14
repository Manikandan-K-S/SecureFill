import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dataCRUD import (
    add_document,
    delete_document,
    update_document,
    view_all,
    view_document,
    similarity_search
)

class SecureFillUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SecureFill Data Management")
        self.root.geometry("800x600")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.add_tab = ttk.Frame(self.notebook)
        self.view_tab = ttk.Frame(self.notebook)
        self.search_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.add_tab, text='Add/Edit Document')
        self.notebook.add(self.view_tab, text='View Documents')
        self.notebook.add(self.search_tab, text='Search Documents')
        
        self.setup_add_tab()
        self.setup_view_tab()
        self.setup_search_tab()

    def setup_add_tab(self):
        # Add Document Form
        ttk.Label(self.add_tab, text="Add/Edit Document", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Document ID (for updates)
        ttk.Label(self.add_tab, text="Document ID (leave empty for new document):").pack(pady=5)
        self.doc_id_entry = ttk.Entry(self.add_tab, width=50)
        self.doc_id_entry.pack(pady=5)
        
        # Attribute
        ttk.Label(self.add_tab, text="Attribute:").pack(pady=5)
        self.attribute_entry = ttk.Entry(self.add_tab, width=50)
        self.attribute_entry.pack(pady=5)
        
        # Value
        ttk.Label(self.add_tab, text="Value:").pack(pady=5)
        self.value_text = scrolledtext.ScrolledText(self.add_tab, width=50, height=5)
        self.value_text.pack(pady=5)
        
        # Metadata
        ttk.Label(self.add_tab, text="Metadata:").pack(pady=5)
        self.metadata_text = scrolledtext.ScrolledText(self.add_tab, width=50, height=3)
        self.metadata_text.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.add_tab)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add/Update Document", command=self.handle_add_update).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def setup_view_tab(self):
        # View Documents
        ttk.Label(self.view_tab, text="View Documents", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Document ID for viewing specific document
        ttk.Label(self.view_tab, text="Enter Document ID to view/delete:").pack(pady=5)
        self.view_id_entry = ttk.Entry(self.view_tab, width=50)
        self.view_id_entry.pack(pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(self.view_tab)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="View Document", command=self.handle_view_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Document", command=self.handle_delete_document).pack(side=tk.LEFT, padx=5)
        
        # View all documents
        ttk.Button(self.view_tab, text="View All Documents", command=self.handle_view_all).pack(pady=5)
        
        # Results area
        self.view_results = scrolledtext.ScrolledText(self.view_tab, width=70, height=20)
        self.view_results.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    def setup_search_tab(self):
        # Search Documents
        ttk.Label(self.search_tab, text="Search Documents", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Search query
        ttk.Label(self.search_tab, text="Enter search query:").pack(pady=5)
        self.search_entry = ttk.Entry(self.search_tab, width=50)
        self.search_entry.pack(pady=5)
        
        # Number of results
        ttk.Label(self.search_tab, text="Number of results:").pack(pady=5)
        self.num_results = ttk.Spinbox(self.search_tab, from_=1, to=10, width=5)
        self.num_results.set(4)
        self.num_results.pack(pady=5)
        
        ttk.Button(self.search_tab, text="Search", command=self.handle_search).pack(pady=5)
        
        # Results area
        self.search_results = scrolledtext.ScrolledText(self.search_tab, width=70, height=20)
        self.search_results.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    def handle_add_update(self):
        doc_id = self.doc_id_entry.get().strip()
        attribute = self.attribute_entry.get().strip()
        value = self.value_text.get("1.0", tk.END).strip()
        metadata = self.metadata_text.get("1.0", tk.END).strip()
        
        if not attribute or not value:
            messagebox.showerror("Error", "Attribute and Value are required!")
            return
        
        try:
            if doc_id:  # Update existing document
                print("IN UPDATE")
                update_document(doc_id, attribute, value, metadata)
                messagebox.showinfo("Success", f"Document {doc_id} updated successfully!")
            else:  # Add new document
                new_id = add_document(attribute, value, metadata)
                messagebox.showinfo("Success", f"Document added successfully with ID: {new_id}")
                self.doc_id_entry.delete(0, tk.END)
                self.doc_id_entry.insert(0, new_id)
            
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Operation failed: {str(e)}")

    def clear_form(self):
        self.attribute_entry.delete(0, tk.END)
        self.value_text.delete("1.0", tk.END)
        self.metadata_text.delete("1.0", tk.END)

    def handle_view_document(self):
        doc_id = self.view_id_entry.get().strip()
        if not doc_id:
            messagebox.showerror("Error", "Please enter a document ID!")
            return
        
        try:
            doc = view_document(doc_id)
            if doc:
                self.view_results.delete("1.0", tk.END)
                self.view_results.insert(tk.END, f"ID: {doc['id']}\n")
                self.view_results.insert(tk.END, f"Value: {doc['value']}\n")
                self.view_results.insert(tk.END, f"Metadata: {doc['metadata']}\n")
            else:
                messagebox.showinfo("Not Found", f"No document found with ID: {doc_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Error viewing document: {str(e)}")

    def handle_delete_document(self):
        doc_id = self.view_id_entry.get().strip()
        if not doc_id:
            messagebox.showerror("Error", "Please enter a document ID!")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete document {doc_id}?"):
            try:
                delete_document(doc_id)
                messagebox.showinfo("Success", f"Document {doc_id} deleted successfully!")
                self.view_id_entry.delete(0, tk.END)
                self.view_results.delete("1.0", tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting document: {str(e)}")

    def handle_view_all(self):
        try:
            docs = view_all()
            self.view_results.delete("1.0", tk.END)
            if docs:
                for doc in docs:
                    self.view_results.insert(tk.END, f"ID: {doc['id']}\n")
                    self.view_results.insert(tk.END, f"Value: {doc['value']}\n")
                    self.view_results.insert(tk.END, f"Metadata: {doc['metadata']}\n")
                    self.view_results.insert(tk.END, "-" * 50 + "\n")
            else:
                self.view_results.insert(tk.END, "No documents found in the database.")
        except Exception as e:
            messagebox.showerror("Error", f"Error viewing documents: {str(e)}")

    def handle_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a search query!")
            return
        
        try:
            num_results = int(self.num_results.get())
            results = similarity_search(query, num_results)
            
            self.search_results.delete("1.0", tk.END)
            if results:
                for i, doc in enumerate(results, 1):
                    self.search_results.insert(tk.END, f"Result {i}:\n")
                    self.search_results.insert(tk.END, f"Content: {doc['content']}\n")
                    self.search_results.insert(tk.END, f"Metadata: {doc['metadata']}\n")
                    self.search_results.insert(tk.END, "-" * 50 + "\n")
            else:
                self.search_results.insert(tk.END, "No similar documents found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error searching documents: {str(e)}")

def main():
    root = tk.Tk()
    app = SecureFillUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
import yaml
import json
import time
import re # Import the regular expression module

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from .modelWrapper import CustomHTTPChatModel

# --- Configuration & Setup (No changes here) ---

def load_config():
    """Loads the API configuration from config.yaml."""
    try:
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("Error: config.yaml not found. Please ensure the file exists.")
        return None

def initialize_llm(config):
    """Initializes the custom LLM instance."""
    if not config: return None
    return CustomHTTPChatModel(
        api_key=config.get("api_key"),
        base_url=config.get("model_server_base_url"),
        workspace_slug=config.get("workspace_slug")
    )

def initialize_vectorstore():
    """Initializes the FAISS vector store from a local directory."""
    try:
        embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return FAISS.load_local(
            folder_path="./DataStore/faiss_index",
            embeddings=embedding_fn,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None

# --- Core LLM Chains (No changes here) ---
analysis_prompt_template = """
You are an expert form analysis engine. Your task is to analyze a list of HTML input fields and a user's instructions to create a structured JSON plan for a vector database search.

User's Instructions:
"{user_prompt}"

List of HTML Input Fields:
{html_fields}

Your goal is to return a single JSON array of objects. Each object must represent one HTML field and contain these keys:
- "original_html": The full, unmodified HTML tag of the input field.
- "description": A clean, human-readable description of what the field is asking for (e.g., "Full Name", "Email Address").
- "search_query": A concise, effective search query for a vector database. This query must reflect the user's instructions.

IMPORTANT:
- If the user provides specific instructions (e.g., "use my work info"), tailor the "search_query" accordingly (e.g., "work email address").
- If the user's instructions are empty or generic, create a generic "search_query" based only on the field's description (e.g., "email address").

Return ONLY the JSON array and nothing else.
"""
analysis_prompt = PromptTemplate.from_template(analysis_prompt_template)

action_plan_prompt_template = """
You are an expert system that generates a JSON "Action Plan" to fill a web form.
Based on the user's request and the context documents retrieved from a database, create a list of actions.

User's Original Request:
"{user_prompt}"

Context Documents (information found from a database search):
{context}

Analyzed Form Fields (with their original HTML):
{fields}

---
Your task is to generate a JSON array of action objects. Each object must have three keys:
1. "selector": A unique and reliable CSS selector for the element, preferring 'id' (e.g., "#userId"), then 'name' (e.g., "[name='userName']"). Use the 'original_html' of each field to find the best selector.
2. "action_type": The type of action to perform. Must be one of: "FILL_TEXT", "SELECT_DROPDOWN", "CHECK_BOX", "SELECT_RADIO".
3. "value": The value to fill or select. For checkboxes, this should be a boolean (true or false).

If no relevant value is found in the context for a field, do not include that field in the final action plan array.
Return ONLY the JSON array and nothing else.
"""
action_plan_prompt = PromptTemplate.from_template(action_plan_prompt_template)


# --- NEW HELPER FUNCTION ---
def extract_json_from_response(text: str):
    """
    Uses a regular expression to find and extract a JSON object or array from a string.
    This is more robust than just finding the first and last brackets.
    """
    # This regex looks for a string starting with '{' or '[' and ending with '}' or ']'
    # It accounts for nested structures.
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

# --- Main Application Logic Functions (UPDATED) ---

def analyze_form_and_create_search_plan(chain, html_fields: list, user_prompt: str):
    """Analyzes the form and user prompt in one call to generate a search plan."""
    print("\n--- 1. Analyzing Form & Creating Search Plan ---")
    prompt_for_llm = user_prompt if user_prompt else "No specific instructions provided. Find the most relevant information."
    
    response_text = chain.invoke({
        "html_fields": json.dumps(html_fields, indent=2),
        "user_prompt": prompt_for_llm
    })
    
    # Use the new robust extractor
    json_string = extract_json_from_response(response_text)
    
    if not json_string:
        print(f"⚠️ Could not find any JSON in the LLM response. Raw Response:\n{response_text}")
        return []

    try:
        analysis_plan = json.loads(json_string)
        print(f"✓ Analysis complete. Generated plan for {len(analysis_plan)} fields.")
        return analysis_plan
    except json.JSONDecodeError:
        print(f"⚠️ Failed to parse extracted JSON. Raw Response:\n{response_text}")
        return []

def search_vector_db(vectorstore, analysis_plan: list, top_k: int = 3):
    """Searches the vector DB using the queries from the analysis plan."""
    print("\n--- 2. Searching Vector Database ---")
    for item in analysis_plan:
        query = item.get('search_query')
        if query and vectorstore:
            results = vectorstore.similarity_search(query, k=top_k)
            item['matched_documents'] = [{"content": doc.page_content} for doc in results]
            print(f"🔍 For query '{query}', found {len(item['matched_documents'])} document(s).")
        else:
            item['matched_documents'] = []
    return analysis_plan

def generate_action_plan(chain, search_results: list, user_prompt: str):
    """Generates the final JSON Action Plan for the browser extension."""
    print("\n--- 3. Generating Final Action Plan ---")
    context = ""
    fields_to_process = []
    
    for item in search_results:
        fields_to_process.append({
            "original_html": item.get('original_html'),
            "description": item.get('description')
        })
        for doc in item.get('matched_documents', []):
            context += f"- {doc['content']}\n"

    if not context.strip():
        print("⚠️ No context found from DB search. Cannot generate a plan.")
        return []

    prompt_for_llm = user_prompt if user_prompt else "No specific instructions provided. Fill with the most relevant information."

    response_text = chain.invoke({
        "context": context,
        "fields": json.dumps(fields_to_process, indent=2),
        "user_prompt": prompt_for_llm
    })

    # Use the new robust extractor here as well
    json_string = extract_json_from_response(response_text)

    if not json_string:
        print(f"⚠️ Could not find any JSON in the LLM action plan response. Raw Response:\n{response_text}")
        return []

    try:
        action_plan = json.loads(json_string)
        print(f"✓ Action Plan generated with {len(action_plan)} steps.")
        return action_plan
    except json.JSONDecodeError:
        print(f"⚠️ Failed to parse extracted JSON from action plan. Raw Response:\n{response_text}")
        return []

# --- Main Execution Block (No changes needed here) ---
if __name__ == "__main__":
    # This part remains the same
    config = load_config()
    llm = initialize_llm(config)
    vectorstore = initialize_vectorstore()
    if not all([config, llm, vectorstore]):
        print("\nExiting due to initialization errors.")
    else:
        analyze_chain = analysis_prompt | llm | StrOutputParser()
        action_plan_chain = action_plan_prompt | llm | StrOutputParser()
        # ... rest of the main block ...

import yaml
import json
import re

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .modelWrapper import CustomHTTPChatModel

# This is the "database". A simple, static context with the user's primary info.
USER_CONTEXT = """
- Name: "Rishi Sunderasan"
- Email Address: rishi2003@gmail.com
- Phone Number: 895625480
- Address: Peelamedu, Coimbatore
"""

# --- THIS IS THE NEW, IMPROVED "MEGA-PROMPT" ---
DIRECT_ACTION_PLAN_PROMPT_TEMPLATE = """
You are an intelligent form-filling assistant. Your primary goal is to **interpret** the user's instructions and provided data to fill out a web form naturally and accurately. You must act as a helpful human completing the form.

--------------------
Here is the primary user data you should use as a basis:
<PrimaryUserData>
{static_context}
</PrimaryUserData>

Here are the user's special instructions and additional context for this specific form:
<AdditionalInstructions>
{dynamic_prompt}
</AdditionalInstructions>

Here are the HTML form fields that need to be filled:
<HtmlFormFields>
{html_fields}
</HtmlFormFields>
--------------------

Your Task:
Generate a JSON array of action objects to fill the form. Each object must have three keys:
1. "selector": A unique and reliable CSS selector for the element. **You MUST prioritize 'id' over 'name'.**
2. "action_type": The type of action to perform. This MUST be one of: "FILL_TEXT", "SELECT_DROPDOWN", "CHECK_BOX".
3. "value": The value to fill or select.

CRITICAL RULES:
- **Interpret, Don't Copy:** When the user provides instructions in `<AdditionalInstructions>`, your job is to understand their intent and generate a helpful, well-formed response. **Do not simply copy their instructions into the form field.**
- For ANY text-based input field (like `type="email"`, `type="text"`, or `textarea`), you MUST use the action_type "FILL_TEXT".
- If a form field does not match any information you have, DO NOT include it in the final JSON array.

**EXAMPLE OF HOW TO INTERPRET INSTRUCTIONS:**
- If a user's instruction in `<AdditionalInstructions>` is: "my inquiry is support and sales please elaborate"
- AND a form field is `<textarea id="inquiry_box" ...>`
- Then the correct "value" in your JSON output should be an elaborated sentence like: `"Hello, I would like to make an inquiry regarding both support and sales. Could you please provide more information on these topics?"`

Return ONLY the JSON array and nothing else.
"""

def extract_json_from_response(text: str):
    """Uses a regular expression to find and extract a JSON object or array from a string."""
    if not text:
        return None
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        return match.group(0)
    return None


class Parser:
    """
    A simplified parser class that holds the AI model and the chain for creating
    an action plan directly, without a vector database.
    """
    def __init__(self):
        """Initializes the LLM and the single LangChain for this process."""
        self.config = self._load_config()
        self.llm = self._initialize_llm()
        if not self.llm:
            raise Exception("Failed to initialize the Language Model.")
        
        # Create the single, powerful prompt template
        self.action_plan_prompt = PromptTemplate.from_template(DIRECT_ACTION_PLAN_PROMPT_TEMPLATE)
        
        # Create the single chain that will do all the work
        self.action_plan_chain = self.action_plan_prompt | self.llm | StrOutputParser()

    def _load_config(self):
        try:
            with open("config.yaml", "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print("Error: config.yaml not found.")
            return None

    def _initialize_llm(self):
        if not self.config: return None
        return CustomHTTPChatModel(
            api_key=self.config.get("api_key"),
            base_url=self.config.get("model_server_base_url"),
            workspace_slug=self.config.get("workspace_slug")
        )

    def create_action_plan(self, html_fields: list, dynamic_prompt: str) -> list:
        """
        Takes the form fields and user prompt, combines them with the static
        user context, and generates a final action plan in a single LLM call.
        """
        print("\n--- Generating Action Plan (Single AI Call) ---")
        
        prompt_for_llm = dynamic_prompt if dynamic_prompt else "No special instructions. Use primary data."

        # Invoke the chain with all the necessary context
        response_text = self.action_plan_chain.invoke({
            "static_context": USER_CONTEXT,
            "dynamic_prompt": prompt_for_llm,
            "html_fields": json.dumps(html_fields, indent=2)
        })

        json_string = extract_json_from_response(response_text)
        
        if not json_string:
            print(f"⚠️ Could not find any JSON in the LLM response. Raw Response:\n{response_text}")
            return []

        try:
            action_plan = json.loads(json_string)
            print(f"✓ Action Plan generated with {len(action_plan)} steps.")
            return action_plan
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse extracted JSON from action plan. Raw Response:\n{response_text}")
            return []

import requests
from typing import List, Any

from pydantic import Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

class CustomHTTPChatModel(BaseChatModel):
    api_key: str = Field(...)
    base_url: str = Field(...)
    workspace_slug: str = Field(...)

    def _call_api(self, message: str) -> str:
        url = f"{self.base_url}/workspace/{self.workspace_slug}/chat"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key
        }
        payload = {
            "message": message,
            "mode": "chat",
            "sessionId": "example-session-id",
            "attachments": []
        }
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json().get("textResponse", "")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any
    ) -> ChatResult:
        user_text = messages[-1].content
        response_text = self._call_api(user_text)
        generation = ChatGeneration(
            message=AIMessage(content=response_text),
            text=response_text
        )
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "custom-http-chat"

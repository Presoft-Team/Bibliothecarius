from pydantic import BaseModel


class LLMTestRequest(BaseModel):
    provider: str
    model: str
    message: str
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7


class LLMTestResponse(BaseModel):
    reply: str

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    analysis_id: int | None = None
    repo_url: str | None = None
    question: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str

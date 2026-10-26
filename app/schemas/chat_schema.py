from pydantic import BaseModel, Field
from typing import List,Optional


class ChatRequest(BaseModel):
    workspace_id: Optional[int] = None
    question: str

    provider: Optional[str] = Field(default=None, min_length=1, max_length=32)
    model: Optional[str] = Field(default=None, min_length=1, max_length=200)


class ChatSource(BaseModel):
    document_id: int
    file_name: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]

from pydantic import BaseModel
from typing import List,Optional


class ChatRequest(BaseModel):
    workspace_id: Optional[int] = None
    question: str


class ChatSource(BaseModel):
    document_id: int
    file_name: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]

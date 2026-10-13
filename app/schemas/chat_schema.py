from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    workspace_id: int
    question: str


class ChatSource(BaseModel):
    document_id: int
    file_name: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]

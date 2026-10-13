import datetime

from pydantic import BaseModel

from app.models.document_model import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    workspace_id: int
    file_name: str
    file_type: str
    file_size: int
    storage_path:str
    status:DocumentStatus
    created_at:datetime
    updated_at:datetime
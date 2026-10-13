import enum

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, Text,Enum
from sqlalchemy.orm import relationship

from app.database.session import Base





class DocumentStatus(str,enum.Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'



class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True,autoincrement=True,index=True,nullable=False)
    workspace_id = Column(Integer,ForeignKey('workspaces.id'),nullable=False)
    file_name=Column(String,nullable=False)
    file_type = Column(String,nullable=False)
    file_size = Column(Integer,nullable=False)
    storage_path = Column(String,nullable=False)
    status = Column(Enum(DocumentStatus),default=DocumentStatus.PENDING, nullable=False)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    document_id = Column(Integer, ForeignKey(
        "documents.id",
        ondelete="CASCADE"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

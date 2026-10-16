from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.dependencies.auth_dependecy import require_user_id
from app.models.workspace_model import Workspace
from app.models.document_model import Document, DocumentChunk
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatSource
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service

router = APIRouter(tags=['AI Chat'], prefix="/api/v1")


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
        chat_in: ChatRequest,
        db: AsyncSession = Depends(get_db),
        current_user: int = Depends(require_user_id)

):


    ws_result = await db.execute(
        select(Workspace).where(Workspace.id == chat_in.workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()

    if not workspace:

        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )



    if workspace.owner_id != current_user:

        raise HTTPException(
            status_code=403,
            detail="Access denied to this workspace"
        )


    question_vector = await embedding_service.get_embedding(chat_in.question)

    if not question_vector:
        raise HTTPException(
            status_code=500,
            detail="Failed to process text embedding for the question"
        )



    chunk_query = (

        select(DocumentChunk, Document.file_name)

        .join(Document, DocumentChunk.document_id == Document.id)

        .where(Document.workspace_id == chat_in.workspace_id)

        .order_by(DocumentChunk.embedding.cosine_distance(question_vector))
        .limit(5)
    )
    chunk_result = await db.execute(chunk_query)

    rows = chunk_result.all()

    if not rows:
        return ChatResponse(
            answer="No processed documents found in this workspace."
                   " Please upload some text, MD, or PDF files first!",
            sources=[]
        )

    contexts = []

    sources = []

    for chunk, file_name in rows:
        contexts.append(chunk.content)
        sources.append(ChatSource(
            document_id=chunk.document_id,
            file_name=file_name,
            chunk_index=chunk.chunk_index
        ))


    ai_answer = await llm_service.generate_rag_answer(
        question=chat_in.question,
        contexts=contexts
    )

    result= ChatResponse(
        answer=ai_answer,
        sources=sources
    )
    return result

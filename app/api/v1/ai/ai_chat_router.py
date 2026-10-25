from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.dependencies.auth_dependecy import require_user_id
from app.models.workspace_model import Workspace
from app.models.document_model import Document, DocumentChunk
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatSource
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service


router = APIRouter(tags=["AI Chat"], prefix="/api/v1")


# Retrieval configuration
MAX_COSINE_DISTANCE = 0.45
MAX_CONTEXT_CHUNKS = 5


def is_general_conversation(question: str) -> bool:
    """
    Identify simple greetings and common conversational questions
    that do not require document retrieval.
    """

    normalized = question.strip().lower()
    normalized = normalized.rstrip("!.,? ")

    general_messages = {
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how are you doing",
        "how's it going",
        "hows it going",
        "what's up",
        "whats up",
        "thanks",
        "thank you",
        "thank you so much",
        "bye",
        "goodbye",
        "who are you",
        "what can you do",
    }

    return normalized in general_messages


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    chat_in: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(require_user_id),
):
    #  Validate the question
    question = chat_in.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty",
        )

    #  Validate workspace access
    ws_result = await db.execute(
        select(Workspace).where(
            Workspace.id == chat_in.workspace_id
        )
    )

    workspace = ws_result.scalar_one_or_none()

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    if workspace.owner_id != current_user:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this workspace",
        )

    #  Skip document retrieval for simple conversations
    if is_general_conversation(question):
        answer = await llm_service.generate_rag_answer(
            question=question,
            contexts=[],
        )

        return ChatResponse(
            answer=answer,
            sources=[],
        )

    #  Generate the question embedding
    question_vector = await embedding_service.get_embedding(
        question
    )

    if not question_vector:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate question embedding",
        )

    #  Retrieve the closest chunks from this workspace
    distance = DocumentChunk.embedding.cosine_distance(
        question_vector
    )

    chunk_query = (
        select(
            DocumentChunk,
            Document.file_name,
            distance.label("distance"),
        )
        .join(
            Document,
            DocumentChunk.document_id == Document.id,
        )
        .where(
            Document.workspace_id == chat_in.workspace_id
        )
        .order_by(distance.asc())
        .limit(MAX_CONTEXT_CHUNKS)
    )

    chunk_result = await db.execute(chunk_query)
    rows = chunk_result.all()

    #  Filter chunks using the cosine-distance threshold
    relevant_rows = [
        row
        for row in rows
        if row.distance is not None
        and float(row.distance) <= MAX_COSINE_DISTANCE
    ]

    #  Prepare relevant contexts and sources
    contexts = []
    sources = []

    for chunk, file_name, _distance in relevant_rows:
        contexts.append(chunk.content)

        sources.append(
            ChatSource(
                document_id=chunk.document_id,
                file_name=file_name,
                chunk_index=chunk.chunk_index,
            )
        )

    #  Generate the answer
    # If no relevant chunks are found, contexts and sources stay empty.
    ai_answer = await llm_service.generate_rag_answer(
        question=question,
        contexts=contexts,
    )

    #  Return the answer and only the retrieved relevant sources
    return ChatResponse(
        answer=ai_answer,
        sources=sources,
    )


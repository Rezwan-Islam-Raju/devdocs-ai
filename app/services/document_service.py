import asyncio
import io
import logging


from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from pypdf import PdfReader
from supabase import create_client, Client
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.document_model import (
    Document,
    DocumentChunk,
    DocumentStatus
)


logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )

        self.bucket_name = settings.SUPABASE_BUCKET_NAME

        self.ai_client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )


    # SUPABASE STORAGE UPLOAD

    async def upload_to_supabase(
        self,
        file_data: bytes,
        storage_path: str,
        content_type: str
    ) :

        loop = asyncio.get_running_loop()

        try:
            await loop.run_in_executor(
                None,
                lambda: self.supabase.storage.from_(
                    self.bucket_name
                ).upload(
                    path=storage_path,
                    file=file_data,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true"
                    },
                ),
            )

            logger.info(
                "File uploaded to Supabase: %s",
                storage_path
            )

            return storage_path

        except Exception:
            logger.exception(
                "Supabase Storage upload failed"
            )
            raise


    # SUPABASE STORAGE DELETE

    async def delete_from_supabase(
        self,
        storage_path: str,
    ) :

        loop = asyncio.get_running_loop()

        try:
            await loop.run_in_executor(
                None,
                lambda: self.supabase.storage.from_(
                    self.bucket_name
                ).remove([storage_path]),
            )

            logger.info(
                "File deleted from Supabase: %s",
                storage_path,
            )

        except Exception:
            logger.exception(
                "Supabase Storage deletion failed"
            )
            raise


    # EXTRACT TEXT

    def extract_text(
        self,
        file_data: bytes,
        file_type: str
    ) :

        file_type = file_type.lower().lstrip(".")
        text = ""

        if file_type == "pdf":

            reader = PdfReader(
                io.BytesIO(file_data)
            )

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        elif file_type in ["txt", "md"]:

            text = file_data.decode(
                "utf-8",
                errors="ignore",
            )

        else:

            raise ValueError(
                f"Unsupported file type: {file_type}"
            )

        return text.strip()

    # CREATE TEXT CHUNKS

    def create_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[str]:

        if not text or not text.strip():
            return []

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero"
            )

        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be non-negative "
                "and smaller than chunk_size"
            )

        words = text.split()
        chunks = []

        start = 0

        while start < len(words):

            end = start + chunk_size

            chunk_words = words[start:end]

            if chunk_words:
                chunks.append(
                    " ".join(chunk_words)
                )

            if end >= len(words):
                break

            start += chunk_size - chunk_overlap

        return chunks


    # GENERATE GEMINI EMBEDDING

    async def generate_text_embedding(
        self,
        text: str
    ) :

        if not text or not text.strip():
            raise ValueError(
                "Cannot generate embedding for empty text"
            )

        loop = asyncio.get_running_loop()

        try:

            result = await loop.run_in_executor(
                None,
                lambda: self.ai_client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=1536,
                    ),
                ),
            )

            if not result or not result.embeddings:
                raise ValueError(
                    "Gemini returned no embedding"
                )

            embedding = result.embeddings[0]

            if not embedding or not embedding.values:
                raise ValueError(
                    "Gemini returned an empty embedding"
                )

            vector = list(embedding.values)

            if len(vector) != 1536:
                raise ValueError(
                    f"Expected 1536 dimensions, "
                    f"received {len(vector)}"
                )

            return vector

        except Exception:
            logger.exception(
                "Gemini embedding generation failed"
            )
            raise


    # PROCESS DOCUMENT PIPELINE


    async def process_document_pipeline(
        self,
        db: AsyncSession,
        doc_id: int,
        file_data: bytes,
        file_type: str
    ) :

        try:

            db_doc = await db.get(
                Document,
                doc_id
            )

            if not db_doc:
                raise ValueError(
                    f"Document {doc_id} was not found"
                )

            db_doc.status = DocumentStatus.PROCESSING

            await db.commit()

            # Extract text
            extracted_text = self.extract_text(
                file_data=file_data,
                file_type=file_type
            )

            if not extracted_text:
                raise ValueError(
                    "No text could be extracted from the document"
                )

            # Split into chunks
            text_chunks = self.create_chunks(
                text=extracted_text,
                chunk_size=500,
                chunk_overlap=50
            )

            if not text_chunks:
                raise ValueError(
                    "No chunks were created from the document"
                )

            # Remove old chunks if reprocessing
            await db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == doc_id
                )
            )

            # Generate embeddings and save chunks
            for index, chunk_content in enumerate(text_chunks):

                vector_data = await self.generate_text_embedding(
                    chunk_content
                )

                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    content=chunk_content,
                    chunk_index=index,
                    embedding=vector_data,
                )

                db.add(db_chunk)

            # Save chunks and update status
            db_doc.status = DocumentStatus.COMPLETED

            await db.commit()

            logger.info(
                "Document %s processed successfully. "
                "Chunks created: %s",
                doc_id,
                len(text_chunks),
            )

        except Exception:

            await db.rollback()

            logger.exception(
                "Document processing failed: %s",
                doc_id,
            )

            # Mark failed if the document still exists
            try:

                failed_doc = await db.get(
                    Document,
                    doc_id,
                )

                if failed_doc:
                    failed_doc.status = DocumentStatus.FAILED
                    await db.commit()

            except Exception:

                await db.rollback()

                logger.exception(
                    "Could not update document failure status"
                )

            raise


# REUSABLE SERVICE INSTANCE

document_service = DocumentService()


import io
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader
from supabase import create_client, Client


import google.generativeai as genai

from app.core.config import settings
from app.models.document_model import Document, DocumentChunk, DocumentStatus


class DocumentService:
    def __init__(self):

        self.supabase: Client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET_NAME


        genai.configure(api_key=settings.GEMINI_API_KEY)

    async def upload_to_supabase(self, file_data: bytes,
                                 storage_path: str,
                                 content_type: str
    ):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": content_type, "x-upsert": "true"}
            )
        )
        return storage_path

    def extract_text(self, file_data: bytes, file_type: str):
        # text extraction from file
        text = ""
        if file_type == "pdf":
            reader = PdfReader(io.BytesIO(file_data))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif file_type in ["txt", "md"]:
            text = file_data.decode("utf-8", errors="ignore")
        return text

    def create_chunks(self, text: str,
                      chunk_size: int = 500,
                      chunk_overlap: int = 50
):
        # small chunk logic
        chunks = []
        words = text.split()

        if len(words) <= chunk_size:
            return [text] if text.strip() else []

        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start += (chunk_size - chunk_overlap)

        return chunks

    async def generate_text_embedding(self, text: str):

        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding generation error: {str(e)}")
            return None

    async def process_document_pipeline(self,
                db: AsyncSession,
                doc_id: int, file_data: bytes,
                file_type: str
):
        try:
            # status processing updated
            db_doc = await db.get(Document, doc_id)
            if not db_doc:
                return
            db_doc.status = DocumentStatus.PROCESSING
            await db.commit()

            # text extract
            extracted_text = self.extract_text(file_data, file_type)

            # text chunk
            text_chunks = self.create_chunks(extracted_text)

            # chunk save database
            for index, chunk_content in enumerate(text_chunks):

                vector_data = await self.generate_text_embedding(chunk_content)

                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    content=chunk_content,
                    chunk_index=index,
                    embedding=vector_data  #
                )
                db.add(db_chunk)

            # status completed
            db_doc.status = DocumentStatus.COMPLETED
            await db.commit()

        except Exception as e:
            await db.rollback()
            db_doc = await db.get(Document, doc_id)
            if db_doc:
                db_doc.status = DocumentStatus.FAILED
                await db.commit()
            print(f"Pipeline error: {str(e)}")


document_service = DocumentService()
